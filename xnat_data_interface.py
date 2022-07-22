import os
from tempfile import TemporaryDirectory
import zipfile
from pyxnat import Interface
import uuid


#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT:
        def __init__(self, username, password):
                # connect to xnat server
                self.interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                          user=username,
                          password=password)

        # disconnect from xnat server to quit session
        def free(self):
                self.interface.disconnect()
                print("successful disconnect from server")


        #---------------------------------------#
        #    XNAT Projects data manipulation    #
        #---------------------------------------#
        # get list of project identifiers       
        def get_all_projects(self):
                return self.interface.select.projects().get()

        # create new project with identifier 'name'
        def create_project(self,name):
                project = self.interface.select.project(name)
                if project.exists() != True:
                        project.create()

        # delete project with identifier 'name'
        def delete_project(self,name):
                project = self.interface.select.project(name)
                if project.exists():
                        project.delete()

        #---------------------------------------#
        #    XNAT files insertion/deletion      #
        #---------------------------------------#
        # extract zip data and feed it to insert_file_project for file upload to a given project
        def insert_zip_into_project(self, project_name, file_path):
                if zipfile.is_zipfile(file_path):
                        with TemporaryDirectory() as tempdir:
                                with zipfile.ZipFile(file_path) as z:
                                        z.extractall(tempdir)
                                        dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])
                                        for f in os.listdir(os.path.join(tempdir, os.listdir(tempdir)[0])): 
                                                #TODO: create new dir for each upload ? currently jpegs are all uploaded to the xnat-dir(resource) 'JPEG' 
                                                self.insert_file_into_project(project_name, os.path.join(dir_path, f))

        # single file upload to given project
        def insert_file_into_project(self, project_name, file_path):
                project = self.interface.select.project(project_name)
                file_id = str(uuid.uuid4())
                if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                        project.resource('JPEG').file(file_id + '.jpeg').insert(file_path, content='image', format='JPEG', tags='image jpeg')
                if file_path.endswith('.json'):
                        project.resource('JSON').file(file_id + '.json').insert(file_path, content='metadata', format='JSON', tags='metadata')
                if file_path.endswith('.nii'):
                        project.resource('NIFTI').file(file_id + '.nii').insert(file_path, content='image', format='NIFTI', tags='image nifti')
                # TODO: upload dicom with subject/experiment data structure 
                if file_path.endswith('.dcm'):
                        project.resource('DICOM').file(file_id + '.dcm').insert(file_path, content='image', format='DICOM', tags='image dicom')
                return file_id

        # remove a file from a given project resource
        def remove_file_from_project(interface, project_name, file_name, resource_name):
                file = interface.select.project(project_name).resource(resource_name).file(file_name)
                if file.exists():
                        file.delete()


    
