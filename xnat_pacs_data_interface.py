import datetime
import os
from tempfile import TemporaryDirectory
import zipfile
from pyxnat import Interface
import uuid
from pacs_data_interface import Connection, Project, Directory, File


#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT(Connection):
        def __init__(self, username, password):
                # connect to xnat server
                self.interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                          user=username,
                          password=password)
                self.user = self.interface._user
                self._projects = self.get_all_projects()

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
        
        # get single project
        def get_project(self, name):
                return self.interface.select.project(name)

        # get single resource
        def get_resource(self, project_name, resource_name):
                return self.interface.select.project(project_name).resource(resource_name)

        # get single file
        def retrieve_file(self, project_name, resource_name, file_name):
                return self.interface.select.project(project_name).resource(resource_name).file(file_name)
    

#---------------------------------------------#
#       XNAT Project interface class          #
#---------------------------------------------#
class XNATProject(Project):
        def __init__(self, connection, name):
                super().__init__(connection, name)
                project = self.connection.get_project(name)
                if project.exists() != True:
                        project.create()
                self._xnat_project_object = project

        @property
        def description(self):
                return self._xnat_project_object.description()

        @property
        def owners(self):
                return self._xnat_project_object.owners()

        @property
        def your_user_role(self):
                return self._xnat_project_object.user_role(self.connection.user)


        # delete project
        def delete_project(self):
                project = self.connection.get_project(self.name)
                if project.exists():
                        project.delete()
        
        # get resource from project
        def get_directory(self, resource_name):
                project = self.connection.get_project(self.name)
                return project.resource(resource_name)

        # get list of project resource objects 
        def get_all_directories(self):
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
                # return XNATFile(resource_name,fle_path)
                return file_id


class XNATResource(Directory):
        def __init__(self, project, name):
                super().__init__(project, name)
                self._xnat_resource_object = project.get_resource(name)

        # remove a resource dir from a project
        def delete_directory(self):
                resource = self._xnat_resource_object
                if resource.exists():
                        resource.delete()
        
        def get_file(self, file_name):
                resource = self._xnat_resource_object
                return resource.file(file_name)

        # get all files from resource
        def get_all_files(self):
                resource = self._xnat_resource_object
                file_names = resource.files().fetchall()
                files = []
                for f in file_names:
                        file = resource.file(f)
                        files.append(file)
                return files


class XNATFile(File):
        def __init__(self,resource,file_name):
                super().__init__(directory=resource,name=file_name)
                self._xnat_file_object = resource.get_file(file_name)

        @property
        def format(self):
                return self._xnat_file_object.format()

        @property
        def size(self):
                return self._xnat_file_object.size()
                
        @property
        def data(self):
                return self._xnat_file_object.size().get()

        # delete file
        def delete_file(self):
                file = self.xnat_file_object
                if file.exists():
                        file.delete()

