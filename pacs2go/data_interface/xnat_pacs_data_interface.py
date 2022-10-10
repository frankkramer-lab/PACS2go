import datetime
import os
from tempfile import TemporaryDirectory
import zipfile
from pyxnat import Interface  # type: ignore
from pyxnat.core.errors import DatabaseError  # type: ignore
import uuid
from typing import List, Sequence, Union


#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT():
    def __init__(self, server:str, username: str, password: str):
        # connect to xnat server 
        #'http://vm204-misit.informatik.uni-augsburg.de:8080'
        self.interface = Interface(server=server,
                                   user=username,
                                   password=password)
        try:
            # try to access usernames to check if connect was successfull
            self.interface.manage.users()
        except DatabaseError:
            # raised if wrong username or password was entered
            raise Exception("Wrong user credentials!")

    @property
    def _kind(self) -> str:
        return "XNAT"

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
class XNATProject():
    def __init__(self, connection: XNAT, name: str) -> None:
        project = connection.interface.select.project(name)
        if project.exists() != True:
            project.create()
        self._xnat_project_object = project
        self.connection = connection
        self.name = name

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
        else:
            raise Exception("Project does not exist/has already been deleted.")

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

    def insert(self, file_path: str, directory_name: str = '') -> Union['XNATDirectory', 'XNATFile']:
        if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
            return self.insert_file_into_project(file_path, directory_name)
        elif zipfile.is_zipfile(file_path):
            return self.insert_zip_into_project(file_path, directory_name)
        else:
            raise Exception("The input is neither a file nor a zip.")
            

    # extract zip data and feed it to insert_file_project for file upload to a given project
    def insert_zip_into_project(self, file_path: str, directory_name: str = '') -> 'XNATDirectory':
        if zipfile.is_zipfile(file_path):
            if directory_name == '':
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
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
        else:
            raise Exception("The input is not a zipfile.")

    # single file upload to given project
    def insert_file_into_project(self, file_path: str, directory_name: str = '') -> 'XNATFile':
        if os.path.exists(file_path):
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
            elif file_path.endswith('.json'):
                file_id = file_id + '.json'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='metadata', format='JSON', tags='metadata')
            elif file_path.endswith('.nii'):
                file_id = file_id + '.nii'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='NIFTI', tags='image nifti')
            # TODO: upload dicom with subject/experiment data structure
            elif file_path.endswith('.dcm'):
                file_id = file_id + '.dcm'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='DICOM', tags='image dicom')
            else:
                raise Exception("This file type is not supported.")
            return XNATFile(XNATDirectory(self, directory_name), file_id)
        else:
            raise Exception("The input is not a file.")


class XNATDirectory():
    def __init__(self, project: XNATProject, name: str) -> None:
        p = project.connection.interface.select.project(project.name)
        self._xnat_resource_object = p.resource(name)
        self.name = name
        self.project = project

    # remove a XNAT resource directory from a project
    def delete_directory(self) -> None:
        directory = self._xnat_resource_object
        if directory.exists():
            directory.delete()
        else:
            raise Exception(
                "Directory does not exist/has already been deleted.")

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


class XNATFile():
    def __init__(self, directory: XNATDirectory, file_name: str) -> None:
        self._xnat_file_object = directory._xnat_resource_object.file(
            file_name)
        self.directory = directory
        self.name = file_name


    @property
    def format(self) -> str:
        return self._xnat_file_object.format()

    @property
    def size(self) -> int:
        return int(self._xnat_file_object.size())

    @property
    def data(self) -> str:
        # retrieve data to a temporary directory
        if self._xnat_file_object.exists():
            with TemporaryDirectory() as tempdir:
                return self._xnat_file_object.get_copy(tempdir + self.name)
        else:
            raise Exception("File data does not exist/ has been deleted.")

    # delete file
    def delete_file(self) -> None:
        file = self._xnat_file_object
        if file.exists():
            file.delete()
        else:
            raise Exception("File does not exist/has already been deleted.")
