import pydicom
import os
import uuid
import datetime


def pseudonymize(path, destination=''):
    if os.path.isdir(path) or os.path.isfile(path):
        """ if os.path.isdir(path):
                # look at the first file to get identity (assuming all files in a directory come from one study)
                first_file = os.listdir(path)[0]
                first_file_path = os.path.join(path, first_file)
                identity = get_vulnerable_data(first_file_path)
                pseudonym = create_pseudonym(identity)
                for filename in os.listdir(path):
                        f = os.path.join(path, filename)
                        # pseudonymize_file(f, destination) """

        if os.path.isfile(path):
            identity = get_vulnerable_data(path)
            pseudonym = create_pseudonym(identity)
            pseudonymize_file(path, destination, pseudonym, identity.keys())
    else:
        raise Exception("invalid path")


def get_vulnerable_data(path):
    ds = pydicom.dcmread(path)
    if hasattr(ds, 'PatientIdentityRemoved'):
        if ds.PatientIdentityRemoved == 'YES':
            raise Exception("Identity has already been removed")
    identity = {}
    identity_attributes = ['PatientID', 'PatientName', 'PatientSex', 'PatientAddress', 'PatientAge', 'PatientBirthDate', 'PatientSize', 'PatientWeight', 'EthnicGroup', 'CountryOfResidence',
                           'RegionOfResidence', 'PatientTelephoneNumbers', 'InstitutionName', 'InstitutionAddress', 'ReferringPhysicianAddress', 'RequestingPhysician', 'ReferringPhysicianName', 'ConsultingPhysicianName', 'PerformingPhysicianName']

    for attr in identity_attributes:
        if hasattr(ds, attr):
            identity[attr] = ds[attr].value
        else:
            identity[attr] = ''
    return identity


def create_pseudonym(identity):
    pseudonym = uuid.uuid4()
    """ with open(f'{pseudonym}.csv', 'w') as csvfile:
        csvfile.write(f"Pseudo-ID, {pseudonym} \n")
        csvfile.write(
            f"Pseudonymization Timestamp, {datetime.datetime.now()} \n")
        for key in identity.keys():
            csvfile.write(f"{key}, {identity[key]} \n") """
    return pseudonym


def pseudonymize_file(path, destination, pseudonym, identity_headers):
    ds = pydicom.dcmread(path)
    for attr in identity_headers:
        if attr == 'PatientID':
            ds[attr].value = str(pseudonym)
        elif hasattr(ds, attr):
            ds[attr].value = ''
        print(ds[attr])


pseudonymize(path=r'/home/main/Desktop/pacs2go/pacs2go/test_data/1-001.dcm')
