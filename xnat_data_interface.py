import datetime
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
                resource_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                if zipfile.is_zipfile(file_path):
                        with TemporaryDirectory() as tempdir:
                                with zipfile.ZipFile(file_path) as z:
                                        z.extractall(tempdir)
                                        dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])
                                        for f in os.listdir(os.path.join(tempdir, os.listdir(tempdir)[0])):                 
                                                self.insert_file_into_project(project_name, os.path.join(dir_path, f), resource_name)

        # single file upload to given project
        def insert_file_into_project(self, project_name, file_path, resource_name=''):
                project = self.interface.select.project(project_name)
                file_id = str(uuid.uuid4()) # file names are unique, duplicate file names can not be inserted
                if resource_name == '':
                        # if no xnat resource directory is given, a new resource with the current timestamp is created
                        resource_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                        project.resource(resource_name).file(file_id + '.jpeg').insert(file_path, content='image', format='JPEG', tags='image jpeg')
                if file_path.endswith('.json'):
                        project.resource(resource_name).file(file_id + '.json').insert(file_path, content='metadata', format='JSON', tags='metadata')
                if file_path.endswith('.nii'):
                        project.resource(resource_name).file(file_id + '.nii').insert(file_path, content='image', format='NIFTI', tags='image nifti')
                # TODO: upload dicom with subject/experiment data structure 
                if file_path.endswith('.dcm'):
                        project.resource(resource_name).file(file_id + '.dcm').insert(file_path, content='image', format='DICOM', tags='image dicom')
                return file_id

        # remove a file from a given project resource
        def remove_file_from_project(self, project_name, file_name, resource_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                if file.exists():
                        file.delete()


        #---------------------------------------#
        #           XNAT file retrieval         #
        #---------------------------------------#
        def retrieve_file(self, project_name, resource_name, file_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                return file
    
        def retrieve_all_files_from_project_resource(self, project_name, resource_name):
                file_names = self.interface.select.project(project_name).resource(resource_name).files().get()
                files = []
                for f in file_names:
                        file = self.retrieve_file(project_name, resource_name, f)
                        files.append(file)
                print(files)

                