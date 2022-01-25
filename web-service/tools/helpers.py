from zipfile import ZipFile
from pyorthanc import Orthanc
from tempfile import TemporaryDirectory
from pydicom.uid import generate_uid
import uuid
import os


def upload_to_orthanc(ds, path, from_web_request):
    # temp directory -> files are only uploaded to orthanc not stored locally
    with TemporaryDirectory() as tmpdirname:
        dicomized_filename = os.path.join(tmpdirname, f'pseudonymized.dcm')
        ds.save_as(dicomized_filename)

        # https://github.com/gacou54/pyorthanc -> documentation
        if from_web_request:
            # if used from inside the web-service (no reverse proxying)
            orthanc = Orthanc('http://orthanc:8042')
        else:
            # if we use the tools as stand-alone functionalities we have to use the public ORTHANC adress (due to reverse proxy)
            orthanc = Orthanc(
                'http://vm204-misit.informatik.uni-augsburg.de/pacs')
        # upload credentials
        orthanc.setup_credentials('uploader', 'pacs2go')
        with open(dicomized_filename, 'rb') as file_handler:
            orthanc.post_instances(file_handler.read())


def save_dicom_file(ds, path, zipped_file, mode):
    # save dicom file
    with TemporaryDirectory() as tmpdirname:
        # save dicom file in temporary directory before writing it to the zip file
        dicomized_filename = os.path.join(
            tmpdirname, f'{mode}_{os.path.splitext(os.path.basename(path))[0]}')
        ds.save_as(dicomized_filename)
        # save/write converted file to zip
        with ZipFile(zipped_file, 'a') as zip:
            zip.write(dicomized_filename, os.path.relpath(
                dicomized_filename, tmpdirname))


def create_new_uids():
        SOPClassUID = generate_uid()
        SOPInstanceUID = generate_uid()
        StudyInstanceUID = generate_uid()
        SeriesInstanceUID = generate_uid()
        PatientID = str(uuid.uuid4())

        uids = [SOPClassUID, SOPInstanceUID,
                StudyInstanceUID, SeriesInstanceUID, PatientID]
        return uids


def check_and_set_destination(path, destination):
    if destination == '':
        if os.path.isfile(path):
            destination = os.path.dirname(path)  # path string without file
        else:
            destination = path
        return destination
    else:
        if not os.path.isdir(destination):
            raise Exception("invalid destination path")
        else:
            return destination