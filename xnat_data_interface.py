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
                self.user = self.interface._user

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
        
        def get_project(self, name):
                return self.interface.select.project(name)


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
                        file_id = file_id + '.jpeg'
                        project.resource(resource_name).file(file_id).insert(file_path, content='image', format='JPEG', tags='image jpeg')
                if file_path.endswith('.json'):
                        file_id = file_id + '.json'
                        project.resource(resource_name).file(file_id).insert(file_path, content='metadata', format='JSON', tags='metadata')
                if file_path.endswith('.nii'):
                        file_id = file_id + '.nii'
                        project.resource(resource_name).file(file_id).insert(file_path, content='image', format='NIFTI', tags='image nifti')
                # TODO: upload dicom with subject/experiment data structure 
                if file_path.endswith('.dcm'):
                        file_id = file_id + '.dcm'
                        project.resource(resource_name).file(file_id).insert(file_path, content='image', format='DICOM', tags='image dicom')
                return file_id

        # remove a file from a given project resource
        def remove_file_from_project(self, project_name, resource_name, file_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                if file.exists():
                        file.delete()

        # remove a resource dir from a project
        def remove_resource_from_project(self, project_name, resource_name):
                resource = self.interface.select.project(project_name).resource(resource_name)
                if resource.exists():
                        resource.delete()

        #---------------------------------------#
        #           XNAT file retrieval         #
        #---------------------------------------#
        # get list of project resource objects 
        def get_all_resources_from_project(self, project_name):
                resource_ids = self.interface.select.project(project_name).resources().fetchall()
                resources = []
                for r in resource_ids:
                        resource = self.interface.select.project(project_name).resource(r)
                        resources.append(resource)
                return resources

        # get single file
        def retrieve_file(self, project_name, resource_name, file_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                return file
    
        # get all files from one resource
        def retrieve_all_files_from_project_resource(self, project_name, resource_name):
                file_names = self.interface.select.project(project_name).resource(resource_name).files().get()
                files = []
                for f in file_names:
                        file = self.retrieve_file(project_name, resource_name, f)
                        files.append(file)
                return files


class XNATProject:
        def __init__(self, connection, name):
                project = connection.get_project(name)
                if project.exists() != True:
                        project.create()
                self.name = project.id()
                self.description = project.description()
                self.owners = project.owners()
                self.your_user_role = project.user_role(connection.user)
                self.connection = connection


        # delete project
        def delete_project(self):
                project = self.connection.get_project(self.name)
                if project.exists():
                        project.delete()
        
