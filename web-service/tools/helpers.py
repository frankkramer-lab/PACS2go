from pyorthanc import Orthanc
from tempfile import TemporaryDirectory
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
            orthanc = Orthanc('http://vm204-misit.informatik.uni-augsburg.de/pacs') 
        # upload credentials
        orthanc.setup_credentials('uploader', 'pacs2go')
        with open(dicomized_filename, 'rb') as file_handler:
            orthanc.post_instances(file_handler.read())
            
