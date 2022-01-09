import pydicom
import os
import uuid


def pseudonymize(path, destination=''):
    if os.path.isdir(path) or os.path.isfile(path):
        if os.path.isfile(path):
            identity = get_vulnerable_data(path)
            pseudonym = create_pseudonym(identity)
            # pseudonymize_file(path, destination)
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
        print(identity)
        return identity


def create_pseudonym(identity):
        pseudonym = uuid.uuid4()
        with open('test.csv', 'w') as csvfile:
                csvfile.write(f"Pseudo-ID, {pseudonym} \n" )
                for key in identity.keys():
                        csvfile.write(f"{key}, {identity[key]} \n")
        return pseudonym


def pseudonymize_file(path, destination, pseudonym):
    ds = pydicom.dcmread(path)
    print(ds)


pseudonymize(path=r'/home/main/Desktop/pacs2go/pacs2go/test_data/1-001.dcm')
