from zipfile import ZipFile
from pyorthanc import Orthanc
from tempfile import TemporaryDirectory
from pydicom.uid import generate_uid
import uuid
import os


# saves a given dicom dataset to a temp directory as dicom file and uploads dicom file to orthanc
def upload_to_orthanc(ds, from_web_request):
    # temp directory -> files are only uploaded to orthanc not stored locally
    with TemporaryDirectory() as tmpdirname:
        dicomized_filename = os.path.join(tmpdirname, f'pseudonymized.dcm')
        ds.save_as(dicomized_filename)

        # https://github.com/gacou54/pyorthanc -> documentation
        if from_web_request:
            # if called from web-service/ from inside the docker container (no reverse proxying)
            orthanc = Orthanc('http://orthanc:8042')
        else:
            # if we use the tools as stand-alone functionalities we have to use the public ORTHANC adress (due to reverse proxy)
            orthanc = Orthanc(
                'http://vm204-misit.informatik.uni-augsburg.de/pacs')
        # upload credentials
        orthanc.setup_credentials('uploader', 'pacs2go')
        with open(dicomized_filename, 'rb') as file_handler:
            orthanc.post_instances(file_handler.read())


# saves a given dicom dataset to a temp directory as dicom file and writes dicom file to given zip path
def save_dicom_file(ds, path, zipped_file, mode, counter=''):
    # save dicom file
    with TemporaryDirectory() as tmpdirname:
        # save dicom file in temporary directory before writing it to the zip file
        dicomized_filename = os.path.join(
            tmpdirname, f'{mode}_{counter}_{os.path.splitext(os.path.basename(path))[0]}')
        ds.save_as(dicomized_filename)
        # save/write converted file to zip
        with ZipFile(zipped_file, 'a') as zip:
            zip.write(dicomized_filename, os.path.relpath(
                dicomized_filename, tmpdirname))


# creates new uids for dicom creation and returns them as a list
def create_new_uids():
        SOPClassUID = generate_uid()
        SOPInstanceUID = generate_uid()
        StudyInstanceUID = generate_uid()
        SeriesInstanceUID = generate_uid()
        PatientID = str(uuid.uuid4())

        uids = [SOPClassUID, SOPInstanceUID,
                StudyInstanceUID, SeriesInstanceUID, PatientID]
        return uids


# checks destination and re-sets it if necessary, returns destination
def check_and_set_destination(path, destination):
    # check if destination is an empty string
    if destination == '':
        if os.path.isfile(path):
            # set destination to directory of the file
            destination = os.path.dirname(path)  # path string without file
        else:
            # set destination to given path
            destination = path
        return destination
    else:
        # checks if given destination is a directory
        if not os.path.isdir(destination):
            raise Exception("invalid destination path")
        else:
            return destination