import pydicom
from pydicom.uid import generate_uid
import os
import uuid
import datetime


def pseudonymize(path, destination=''):
    if os.path.isdir(path) or os.path.isfile(path):
        # create new uids (original and pseudonymized version should not have the same uids -> OHIF and ORTHANC problems)
        SOPClassUID = generate_uid()
        SOPInstanceUID = generate_uid()
        StudyInstanceUID = generate_uid()
        SeriesInstanceUID = generate_uid()
        PatientID = str(uuid.uuid4())

        uids = [SOPClassUID, SOPInstanceUID,
                StudyInstanceUID, SeriesInstanceUID, PatientID]

        if destination == '':
            if os.path.isfile(path):
                dir_path = os.path.dirname(path)  # path string without file
                destination = os.path.join(dir_path, 'pseudonymized')
            else:
                destination = os.path.join(path, 'pseudonymized')
            if not os.path.exists(destination):
                os.mkdir(destination)
            
        if os.path.isdir(path):
                i = 1
                for filename in os.listdir(path):
                        f = os.path.join(path, filename)
                        if os.path.isfile(f) and f.endswith(".dcm"):
                            if i==1:
                                # look at the first file to get identity (assuming all files in a directory come from one study)
                                identity = get_vulnerable_data(f)
                                pseudonym = create_pseudonym(identity,destination)
                            pseudonymize_file(f, destination, uids, pseudonym, identity.keys(),i)
                            i += 1

        if os.path.isfile(path):
            identity = get_vulnerable_data(path)
            pseudonym = create_pseudonym(identity,destination)
            pseudonymize_file(path, destination, uids,
                              pseudonym, identity.keys())
    else:
        raise Exception("invalid path")


def get_vulnerable_data(path):
    ds = pydicom.dcmread(path)
    """ if hasattr(ds, 'PatientIdentityRemoved'):
        if ds.PatientIdentityRemoved == 'YES':
            raise Exception("Identity has already been removed") """
    # identity dict which will contain tag names and values
    identity = {}
    # attributes according to: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4636522/
    # + InstanceCreationDate/Time + AdditionalPatientHistory + EthnicGroup
    # correct spelling for pydicom found in: https://github.com/pydicom/pydicom/blob/master/pydicom/_dicom_dict.py
    identity_attributes = ['PatientID', 'InstanceCreationDate', 'InstanceCreationTime', 'StudyDate', 'SeriesDate', 'AquisitionDate',
                           'ContentDate', 'OverlayDate', 'CurveDate', 'AcquisitionDatetime', 'StudyTime', 'SeriesTime', 'AcquisitionTime',
                           'ContentTime', 'OverlayTime', 'CurveTime', 'AccessionNumber', 'InstitutionName', 'InstitutionAddress',
                           'ReferringPhysicianName', 'ReferringPhysicianAddress', 'ReferringPhysicianTelephoneNumbers',
                           'ReferringPhysicianIdentificationSequence', 'InstitutionalDepartmentName', 'PhysiciansOfRecord',
                           'PhysiciansOfRecordIdentificationSequence', 'PerformingPhysiciansName', 'PerformingPhysicianIdentificationSequence',
                           'NameOfPhysiciansReadingStudy', 'PhysiciansReadingStudyIdentificationSequence', 'OperatorsName', 'PatientName',
                           'IssuerOfPatientID', 'PatientBirthDate', 'PatientBirthTime', 'PatientSex', 'OtherPatientIDs', 'OtherPatientNames',
                           'PatientBirthName', 'PatientAge', 'EthnicGroup', 'AdditionalPatientHistory', 'PatientAddress', 'PatientMotherBirthName',
                           'CountryOfResidence', 'RegionOfResidence', 'PatientTelephoneNumbers', 'StudyID', 'CurrentPatientLocation',
                           'PatientInstitutionResidence', 'DateTime', 'Date', 'Time', 'PersonName']
    for attr in identity_attributes:
        if hasattr(ds, attr):
            identity[attr] = ds[attr].value
        else:
            identity[attr] = ''
    return identity


def create_pseudonym(identity, destination):
    pseudonym = uuid.uuid4()
    csv_path = os.path.join(destination, f"{pseudonym}.csv")
    with open(csv_path, 'w') as csvfile:
        csvfile.write(f"Pseudo-ID, {pseudonym} \n")
        csvfile.write(
            f"Pseudonymization Timestamp, {datetime.datetime.now()} \n")
        for key in identity.keys():
            csvfile.write(f"{key}, {identity[key]} \n")
    return pseudonym


def pseudonymize_file(path, destination, uids, pseudonym, identity_headers, instance_index=0):
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
                delattr(ds, attr)
    ds.PatientIdentityRemoved = 'YES'
    ds.SOPClassUID = uids[0]
    ds.SOPInstanceUID = str(uids[1]) + '.' + str(instance_index)
    ds.StudyInstanceUID = uids[2]
    ds.SeriesInstanceUID = str(uids[3])

    print("pixal data may be identifying and vendor tags (uneven number) may contain identifying information")

    dicomized_filename = os.path.join(destination, f'{instance_index}.dcm')
    ds.save_as(dicomized_filename)


# pseudonymize(path=r'/home/main/Desktop/pacs2go/pacs2go/test_data/1-001.dcm')
# pseudonymize(path=r'/home/main/Desktop/images/pseudo_test/CT THINS')
