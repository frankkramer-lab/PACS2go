import datetime
import os
from tempfile import TemporaryDirectory
import zipfile
from django.db import DatabaseError
from pyxnat import Interface # type: ignore
from pyxnat.core.errors import DatabaseError # type: ignore
import uuid
from pacs_data_interface import Connection, Project, Directory, File
from typing import List, Optional, Sequence


#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT(Connection):
    def __init__(self, username: str, password: str):
        # connect to xnat server
        self.interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                                   user=username,
                                   password=password)
        super().__init__()
        try:
            # try to access usernames to check if connect was successfull
            self.interface.manage.users()
        except DatabaseError:
            # raised if wrong username or password was entered
            raise IOError("Wrong user credentials!")

        

    @property
    def user(self) -> str:
        return self.interface._user

    def __enter__(self) -> 'XNAT':
        return self

    def __exit__(self, type, value, traceback) -> None:
        # disconnect from xnat server to quit session
        try:
            self.interface.disconnect()
            print("Successful disconnect from server!")
        except DatabaseError:
            # this is the case if the connection was not possible in the first place
            print("No disconnect possible.")

    #---------------------------------------#
    #      XNAT Projects data retrieval     #
    #---------------------------------------#
    # get single project
    def get_project(self, name: str) -> 'XNATProject':
        return XNATProject(self, name)

    # get list of project identifiers
    def get_all_projects(self) -> Sequence['XNATProject']:
        project_names = self.interface.select.projects().fetchall()
        if len(project_names) == 0:
            return []
        projects = []
        for p in project_names:
            project = self.get_project(p)
            projects.append(project)
        return projects


#---------------------------------------------#
#       XNAT Project interface class          #
#---------------------------------------------#
class XNATProject(Project):
    def __init__(self, connection: XNAT, name: str) -> None:
        project = connection.interface.select.project(name)
        if project.exists() != True:
            project.create()
        self._xnat_project_object = project
        super().__init__(connection, name)

    @property
    def description(self) -> str:
        return self._xnat_project_object.description()

    @property
    def owners(self) -> List[str]:
        return self._xnat_project_object.owners()

    @property
    def your_user_role(self) -> str:
        return self._xnat_project_object.user_role(self.connection.user)

    # delete project
    def delete_project(self) -> None:
        project = self._xnat_project_object
        if project.exists():
            project.delete()

    # get directory from project
    def get_directory(self, directory_name: str) -> 'XNATDirectory':
        return XNATDirectory(self, directory_name)

    # get list of project directory objects
    def get_all_directories(self) -> Sequence['XNATDirectory']:
        directory_names = []
        # get directory names
        for r in self._xnat_project_object.resources():
            directory_names.append(r.label())
        if len(directory_names) == 0:
            return []
        else:
            directories = []
            for r in directory_names:
                directory = self.get_directory(r)
                directories.append(directory)
            return directories

    # extract zip data and feed it to insert_file_project for file upload to a given project
    def insert_zip_into_project(self, file_path: str, directory_name: str ='') -> 'XNATDirectory':
        if directory_name == '':
            directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
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
                        self.insert_file_into_project(
                            os.path.join(dir_path, f), directory_name)
        return XNATDirectory(self, directory_name)

    # single file upload to given project
    def insert_file_into_project(self, file_path: str, directory_name: str ='') -> 'XNATFile':
        project = self._xnat_project_object
        # file names are unique, duplicate file names can not be inserted
        file_id = str(uuid.uuid4())
        if directory_name == '':
            # if no xnat resource directory is given, a new directory with the current timestamp is created
            directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            file_id = file_id + '.jpeg'
            project.resource(directory_name).file(file_id).insert(
                file_path, content='image', format='JPEG', tags='image jpeg')
        if file_path.endswith('.json'):
            file_id = file_id + '.json'
            project.resource(directory_name).file(file_id).insert(
                file_path, content='metadata', format='JSON', tags='metadata')
        if file_path.endswith('.nii'):
            file_id = file_id + '.nii'
            project.resource(directory_name).file(file_id).insert(
                file_path, content='image', format='NIFTI', tags='image nifti')
        # TODO: upload dicom with subject/experiment data structure
        if file_path.endswith('.dcm'):
            file_id = file_id + '.dcm'
            project.resource(directory_name).file(file_id).insert(
                file_path, content='image', format='DICOM', tags='image dicom')
        return XNATFile(XNATDirectory(self, directory_name), file_id)


class XNATDirectory(Directory):
    def __init__(self, project: XNATProject, name: str) -> None:
        p = project.connection.interface.select.project(project.name)
        self._xnat_resource_object = p.resource(name)
        super().__init__(project, name)

    # remove a XNAT resource directory from a project
    def delete_directory(self) -> None:
        directory = self._xnat_resource_object
        if directory.exists():
            directory.delete()

    def get_file(self, file_name: str) -> 'XNATFile':
        return XNATFile(self, file_name)

    # get all files from directory
    def get_all_files(self) -> Sequence['XNATFile']:
        directory = self._xnat_resource_object
        file_names = directory.files().fetchall()
        files = []
        for f in file_names:
            file = self.get_file(f)
            files.append(file)
        return files


class XNATFile(File):
    def __init__(self, directory: XNATDirectory, file_name: str) -> None:
        self._xnat_file_object = directory._xnat_resource_object.file(
            file_name)
        super().__init__(directory=directory, name=file_name)

    @property
    def format(self) -> str:
        return self._xnat_file_object.format()

    @property
    def size(self) -> int:
        return int(self._xnat_file_object.size())

    @property
    def data(self) -> str:
        # retrieve data to a temporary directory
        with TemporaryDirectory() as tempdir:
            return self._xnat_file_object.get_copy(tempdir + self.name)

    # delete file
    def delete_file(self) -> None:
        file = self._xnat_file_object
        if file.exists():
            file.delete()
