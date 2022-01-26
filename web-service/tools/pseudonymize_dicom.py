from helpers import upload_to_orthanc, save_dicom_file, create_new_uids, check_and_set_destination
from tempfile import TemporaryDirectory
from importlib_metadata import zipp
import pydicom
import os
import uuid
import datetime
from zipfile import ZipFile

# to import project functionalities
import sys
sys.path.append('./tools')

# pseudonymization function for both directories and single files
def pseudonymize(path, destination='', upload=False, from_web_request=False):
    if os.path.isdir(path) or os.path.isfile(path):
        # create new uids (original and pseudonymized version should not have the same uids -> OHIF and ORTHANC problems)
        uids = create_new_uids()

        # destination folder
        destination = check_and_set_destination(path, destination)

        # create zipped_file location -> for no upload (save to destination) mode, data will be zipped
        zipped_file = os.path.join(destination, "pseudonymized.zip")

        # pseudonymizes a whole directory of dicom files (one dicom series)
        if os.path.isdir(path):
            i = 1
            for filename in os.listdir(path):
                f = os.path.join(path, filename)
                if os.path.isfile(f) and f.endswith(".dcm"):
                    if i == 1:
                        # look at the 1st file of the directory to extract the identity
                        # (assuming all files in a directory come from one study)
                        identity = get_vulnerable_data(f)
                        pseudonym = create_pseudonym(identity, zipped_file)
                    ds = pseudonymize_file(
                        f, uids, pseudonym, identity.keys(), i)
                    if upload:
                        upload_to_orthanc(ds, from_web_request)
                    else:
                        save_dicom_file(ds, f, zipped_file, "pseudonymized")
                    i += 1

        # pseudonymizes a single dicom file
        if os.path.isfile(path):
            identity = get_vulnerable_data(path)
            pseudonym = create_pseudonym(identity, zipped_file)
            ds = pseudonymize_file(path, uids, pseudonym, identity.keys())
            if upload:
                upload_to_orthanc(ds, from_web_request)
            else:
                save_dicom_file(ds, path, zipped_file, "pseudonymized")
        # returning the zip file is necessary for web-service, otherwise the zip was already saved in 'destination'
        return zipped_file
    else:
        raise Exception("invalid path")


# extracts and returns identifying data (as a dictionary)
def get_vulnerable_data(path):
    ds = pydicom.dcmread(path)
    # identity dict which will contain tag names and values
    identity = {}
    # attributes according to: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4636522/ + InstanceCreationDate/Time + AdditionalPatientHistory + EthnicGroup + PatientWeight
    # correct attribute spellings for pydicom found in: https://github.com/pydicom/pydicom/blob/master/pydicom/_dicom_dict.py
    identity_attributes = ['PatientID', 'InstanceCreationDate', 'InstanceCreationTime', 'StudyDate', 'SeriesDate', 'AcquisitionDate',
                           'ContentDate', 'OverlayDate', 'CurveDate', 'StudyTime', 'SeriesTime', 'AcquisitionTime',
                           'ContentTime', 'OverlayTime', 'CurveTime', 'AccessionNumber', 'InstitutionName', 'InstitutionAddress',
                           'ReferringPhysicianName', 'ReferringPhysicianAddress', 'ReferringPhysicianTelephoneNumbers',
                           'ReferringPhysicianIdentificationSequence', 'InstitutionalDepartmentName', 'PhysiciansOfRecord',
                           'PhysiciansOfRecordIdentificationSequence', 'PerformingPhysiciansName', 'PerformingPhysicianIdentificationSequence',
                           'NameOfPhysiciansReadingStudy', 'PhysiciansReadingStudyIdentificationSequence', 'OperatorsName', 'PatientName',
                           'IssuerOfPatientID', 'PatientBirthDate', 'PatientBirthTime', 'PatientSex', 'OtherPatientIDs', 'OtherPatientNames',
                           'PatientBirthName', 'PatientAge', 'PatientWeight', 'EthnicGroup', 'AdditionalPatientHistory', 'PatientAddress', 'PatientMotherBirthName',
                           'CountryOfResidence', 'RegionOfResidence', 'PatientTelephoneNumbers', 'StudyID', 'CurrentPatientLocation',
                           'PatientInstitutionResidence', 'DateTime', 'Date', 'Time', 'PersonName']
    for attr in identity_attributes:
        if hasattr(ds, attr):
            identity[attr] = ds[attr].value
        else:
            identity[attr] = ''
    return identity


# saves identity (+ mapping to its pseudonym) in a csv file, returns pseudonym
def create_pseudonym(identity, zipped_file):
    pseudonym = uuid.uuid4()
    with TemporaryDirectory() as tmpdirname:
        # write csv file to temporary directory
        csv_name = f"{pseudonym}.csv"
        csv_path = os.path.join(tmpdirname, csv_name)
        # write pseudonym and identifiying information to csv
        with open(csv_path, 'w') as csvfile:
            csvfile.write(f"Pseudo-ID, {pseudonym} \n")
            csvfile.write(
                f"Pseudonymization Timestamp, {datetime.datetime.now()} \n")
            for key in identity.keys():
                csvfile.write(f"{key}, {identity[key]} \n")

        # write csv to zip file
        with ZipFile(zipped_file, 'w') as zip:
            zip.write(csv_path, os.path.relpath(csv_path, tmpdirname))

    return pseudonym


# removes the identity from a dicom file and replaces it with the pseudonym
def pseudonymize_file(path, uids, pseudonym, identity_headers, instance_index=0):
    ds = pydicom.dcmread(path)
    # remove or replace conform to DICOM supplement 142
    for attr in identity_headers:
        if hasattr(ds, attr):
            # often required and important for ORTHANC lookup
            if attr == 'PatientID' or attr == 'PatientName' or attr == 'StudyID':
                ds[attr].value = str(pseudonym)
            # since Date and Time values are often required, they are set to default values
            elif attr.__contains__('Date'):
                ds[attr].value = '19000101'
            elif attr.__contains__('Time'):
                ds[attr].value = '000000'
            else:
                # remove attribute from dicom file
                delattr(ds, attr)

    ds.PatientIdentityRemoved = 'YES'

    # new uids for pseudonymized version
    ds.SOPClassUID = uids[0]
    ds.SOPInstanceUID = str(uids[1]) + '.' + str(instance_index)
    ds.StudyInstanceUID = uids[2]
    ds.SeriesInstanceUID = str(uids[3])

    return ds



# how to use pseudonymize_dicom:
# single dcm file, no upload:
# pseudonymize(path=r'/home/main/Desktop/pacs2go/pacs2go/test_data/1-001.dcm')
# directory with dcm files, with upload to ORTHANC
# pseudonymize(path=r'/home/main/Desktop/images/pseudo_test/CT THINS', upload=True)
