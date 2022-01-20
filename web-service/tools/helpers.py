from pyorthanc import Orthanc
from tempfile import TemporaryDirectory
import os

def upload_to_orthanc(ds, path):
    # temp directory -> files are only uploaded to orthanc not stored locally
    with TemporaryDirectory(dir="/home/main/Desktop/pacs2go/pacs2go") as tmpdirname:
        dicomized_filename = os.path.join(
            tmpdirname, f'pseudonymized_{os.path.basename(path)}')
        ds.save_as(dicomized_filename)

        # https://github.com/gacou54/pyorthanc -> documentation 
        orthanc = Orthanc('http://localhost/pacs')
        orthanc.setup_credentials('uploader', 'pacs2go')

        with open(dicomized_filename, 'rb') as file_handler:
            orthanc.post_instances(file_handler.read())