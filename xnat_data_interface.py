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

        def __enter__(self):
                return self

        def __exit__(self, type, value, traceback):
                # disconnect from xnat server to quit session
                self.interface.disconnect()
                print("successful disconnect from server")

        #---------------------------------------#
        #      XNAT Projects data retrieval     #
        #---------------------------------------#
        # get list of project identifiers       
        def get_all_projects(self):
                return self.interface.select.projects().get()
        
        def get_project(self, name):
                return self.interface.select.project(name)


        #---------------------------------------#
        #    XNAT files insertion/deletion      #
        #---------------------------------------#
        # remove a file from a given project resource
        def remove_file_from_project(self, project_name, resource_name, file_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                if file.exists():
                        file.delete()

        #---------------------------------------#
        #           XNAT file retrieval         #
        #---------------------------------------#
        # get single file
        def retrieve_file(self, project_name, resource_name, file_name):
                file = self.interface.select.project(project_name).resource(resource_name).file(file_name)
                return file
    

#---------------------------------------------#
#       XNAT Project interface class          #
#---------------------------------------------#
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
        
        # get resource from project
        def get_resource(self, resource_name):
                project = self.connection.get_project(self.name)
                return project.resource(resource_name)

        # get list of project resource objects 
        def get_resources(self):
                project = self.connection.get_project(self.name)
                resource_ids = project.resources().fetchall()
                resources = []
                for r in resource_ids:
                        resource = project.resource(r)
                        resources.append(resource)
                return resources

        # extract zip data and feed it to insert_file_project for file upload to a given project
        def insert_zip_into_project(self, file_path):
                resource_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                if zipfile.is_zipfile(file_path):
                        with TemporaryDirectory() as tempdir:
                                with zipfile.ZipFile(file_path) as z:
                                        z.extractall(tempdir)
                                        dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])
                                        # get all files, even those within a lower-level directory
                                        onlyfiles = []
                                        for (dirpath, dirnames, filenames) in os.walk(dir_path):
                                                onlyfiles.extend(filenames)
                                        for f in onlyfiles:  
                                              self.insert_file_into_project(os.path.join(dir_path, f), resource_name)

        # single file upload to given project
        def insert_file_into_project(self, file_path, resource_name=''):
                project = self.connection.get_project(self.name)
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


class XNATResource:
        def __init__(self, project, name):
                resource = project.get_resource(name)
                self.id = resource.id()
                self.name = resource.label()
                self.number_of_files = len(resource.files().fetchall())
                self.project = project

        # get all files from resource
        def get_all_files(self):
                resource = self.project.get_resource(self.name)
                file_names = resource.files().fetchall()
                files = []
                for f in file_names:
                        file = resource.file(f)
                        files.append(file)
                return files

        # remove a resource dir from a project
        def remove_resource(self):
                resource = self.project.get_resource(self.name)
                if resource.exists():
                        resource.delete()