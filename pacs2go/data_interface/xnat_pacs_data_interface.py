import datetime
import os
import uuid
import zipfile
from tempfile import TemporaryDirectory
from typing import List
from typing import Sequence
from typing import Union

from pyxnat import Interface  # type: ignore
from pyxnat.core.errors import DatabaseError  # type: ignore


#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT():
    def __init__(self, server: str, username: str, password: str):
        # Connect to xnat server
        # 'http://localhost:8888'
        self.interface = Interface(server=server,
                                   user=username,
                                   password=password)

        try:
            # Try to access usernames to check if connect was successfull
            self.interface.manage.users()

        except DatabaseError:
            # Raised if wrong username or password was entered
            raise Exception("Wrong user credentials!")

    @property
    def _kind(self) -> str:
        return "XNAT"

    @property
    def user(self) -> str:
        return str(self.interface._user)

    def __enter__(self) -> 'XNAT':
        return self

    def __exit__(self, type, value, traceback) -> None:
        # Disconnect from xnat server to quit session
        try:
            self.interface.disconnect()
            print("Successful disconnect from server!")

        except DatabaseError:
            # This is the case if the connection was not possible in the first place
            print("No disconnect possible.")

    #---------------------------------------#
    #      XNAT Projects data retrieval     #
    #---------------------------------------#
    # Get single project
    def get_project(self, name: str) -> 'XNATProject':
        if self.interface.select.project(name).exists():
            return XNATProject(self, name)

        else:
            raise Exception(
                f"A project with this name ({name}) does not exist.")

    # Get list of project identifiers
    def get_all_projects(self) -> List['XNATProject']:
        project_names = self.interface.select.projects().fetchall()

        if len(project_names) == 0:
            return []

        projects = []
        for p in project_names:
            project = self.get_project(p)
            projects.append(project)

        return projects

    def get_directory(self, project_name: str, directory_name: str) -> 'XNATDirectory':
        # See if directory exists in XNAT
        if self.interface.select.project(project_name).resource(directory_name).exists():
            return XNATDirectory(XNATProject(self, project_name), directory_name)
        else:
            raise Exception(
                "A Directory with the specified properties does not exists.")

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> 'XNATFile':
        if self.interface.select.project(project_name).resource(directory_name).file(file_name).exists():
            return XNATFile(XNATDirectory(XNATProject(self, project_name), directory_name), file_name)
        else:
            raise Exception(
                f"No file called {file_name} in Project {project_name}, Directory {directory_name}.")


#---------------------------------------------#
#       XNAT Project interface class          #
#---------------------------------------------#
class XNATProject():
    def __init__(self, connection: XNAT, name: str) -> None:
        project = connection.interface.select.project(name)

        if project.exists() != True:
            try:
                project.create()

            except:
                raise Exception(
                    "This project name has been used with your XNAT server before, please choose another.")

        self._xnat_project_object = project
        self.connection = connection
        self.name = name

    @property
    def description(self) -> str:
        return self._xnat_project_object.description()

    def set_description(self, description_string: str) -> None:
        # Set new description to given string
        self._xnat_project_object.attrs.set('description', description_string)

    @property
    def keywords(self) -> str:
        return self._xnat_project_object.attrs.get('keywords')

    def set_keywords(self, keyword_string: str) -> None:
        # new_keyword = self.keywords + ", " + keyword_string
        # Set new description to given string
        self._xnat_project_object.attrs.set('keywords', keyword_string)

    @property
    def owners(self) -> List[str]:
        return self._xnat_project_object.owners()

    @property
    def your_user_role(self) -> str:
        return self._xnat_project_object.user_role(self.connection.user)

    def exists(self) -> bool:
        # Check if project exists on XNAT server
        return self._xnat_project_object.exists()

    def delete_project(self) -> None:
        if self.exists():
            # Delete project
            self._xnat_project_object.delete()

        else:
            raise Exception(
                f"Project {self.name} does not exist/has already been deleted.")

    def get_directory(self, directory_name: str) -> 'XNATDirectory':
        # Get directory
        return XNATDirectory(self, directory_name)

    def get_all_directories(self) -> Sequence['XNATDirectory']:
        directory_names = []
        # Get directory names
        for r in self._xnat_project_object.resources():
            directory_names.append(r.label())

        if len(directory_names) == 0:
            return []

        else:
            directories = []
            # Get a list of all directories
            for r in directory_names:
                directory = self.get_directory(r)
                directories.append(directory)

            return directories

    def download(self, destination: str) -> str:
        # Create a zip file for the project
        zip_destination = os.path.join(destination, f'{self.name}.zip')

        with TemporaryDirectory() as tempdir:
            # Iterate over directories to download them and write them to the project zip
            for d in self.get_all_directories():
                directory_filename = d.download(tempdir)

                with zipfile.ZipFile(zip_destination, 'a') as zip:
                    zip.write(directory_filename ,os.path.relpath(directory_filename, tempdir))

        return zip_destination

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['XNATDirectory', 'XNATFile']:
        # File path leads to a single file
        if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
            return self.insert_file_into_project(file_path, directory_name, tags_string)

        # File path equals a zip file
        elif zipfile.is_zipfile(file_path):
            return self.insert_zip_into_project(file_path, directory_name, tags_string)

        else:
            raise Exception("The input is neither a file nor a zip.")

    def insert_zip_into_project(self, file_path: str, directory_name: str = '', tags_string='') -> 'XNATDirectory':
        # Extract zip data and feed it to insert_file_project
        if zipfile.is_zipfile(file_path):
            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                # This must be done here for zips bc otherwise all files end up in different directories
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            with TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(file_path) as z:
                    z.extractall(tempdir)
                    dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])

                    # Get all files, even those within a lower-level directory
                    onlyfiles = []
                    for (dirpath, dirnames, filenames) in os.walk(dir_path):
                        onlyfiles.extend(filenames)

                    # Insert files
                    for f in onlyfiles:
                        self.insert_file_into_project(
                            os.path.join(dir_path, f), directory_name, tags_string)

            return XNATDirectory(self, directory_name)

        else:
            raise Exception("The input is not a zipfile.")

    # Single file upload to given project
    def insert_file_into_project(self, file_path: str, directory_name: str = '', tags_string: str = '') -> 'XNATFile':
        if os.path.exists(file_path):
            project = self._xnat_project_object
            # Rile names are unique, duplicate file names can not be inserted
            file_id = str(uuid.uuid4())

            # Lowercase file_path so things like '.PNG' aren't a problem
            lower_file_path = file_path.lower()

            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            if lower_file_path.endswith('.jpg') or lower_file_path.endswith('.jpeg'):
                file_id = file_id + '.jpeg'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='JPEG', tags='Image, JPEG, ' + tags_string)

            elif lower_file_path.endswith('.png'):
                file_id = file_id + '.png'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='PNG', tags='Image, PNG, ' + tags_string)

            elif lower_file_path.endswith('.nii'):
                file_id = file_id + '.nii'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='NIFTI', tags='Image, NIFTI, ' + tags_string)

            elif lower_file_path.endswith('.dcm'):
                file_id = file_id + '.dcm'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='DICOM', tags='Image, DICOM, ' + tags_string)

            elif lower_file_path.endswith('.tiff'):
                file_id = file_id + '.tiff'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='image', format='TIFF', tags='Image, TIFF, ' + tags_string)

            elif lower_file_path.endswith('.csv'):
                file_id = file_id + '.csv'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='metadata', format='CSV', tags='Metadata, CSV, ' + tags_string)

            elif lower_file_path.endswith('.json'):
                file_id = file_id + '.json'
                project.resource(directory_name).file(file_id).insert(
                    file_path, content='metadata', format='JSON', tags='Metadata, JSON, ' + tags_string)

            else:
                raise Exception("This file type is not supported.")

            return XNATFile(XNATDirectory(self, directory_name), file_id)

        else:
            raise Exception("The input is not a file.")


class XNATDirectory():
    def __init__(self, project: XNATProject, name: str) -> None:
        # Attention: Directories are originally called 'Resources' in the XNAT Universe
        self._xnat_resource_object = project._xnat_project_object.resource(
            name)
        if not self._xnat_resource_object:
            raise Exception(f"A directory called {name} does not exist.")
        self.name = name
        self.project = project

    @property
    def contained_file_tags(self) -> str:
        # Retrieved attributes https://wiki.xnat.org/display/XAPI/Subject+Resource+API
        return self._xnat_resource_object._getcell("tags")

    @property
    def number_of_files(self) -> str:
        return self._xnat_resource_object._getcell("file_count")

    # Check if directory/recource exists on XNAT server
    def exists(self) -> bool:
        return self._xnat_resource_object.exists()

    def delete_directory(self) -> None:
        if self.exists():
            # Delete XNAT resource directory
            self._xnat_resource_object.delete()

        else:
            raise Exception(
                "Directory does not exist/has already been deleted.")

    def get_file(self, file_name: str) -> 'XNATFile':
        # Get specific file, via name
        return XNATFile(self, file_name)

    def get_all_files(self) -> List['XNATFile']:
        directory = self._xnat_resource_object
        file_names = directory.files().fetchall()
        files = []

        # Get all files from directory
        for f in file_names:
            file = self.get_file(f)
            files.append(file)

        return files

    def download(self, destination: str) -> str:
        # Download directory as zip file and return download location
        return self._xnat_resource_object.get(destination)


class XNATFile():
    def __init__(self, directory: XNATDirectory, file_name: str) -> None:
        self._xnat_file_object = directory._xnat_resource_object.file(
            file_name)
        if not self._xnat_file_object:
            raise Exception(f"A file called {file_name} does not exist.")
        self.directory = directory
        self.name = file_name

    @property
    def format(self) -> str:
        return self._xnat_file_object.format()

    @property
    def tags(self) -> str:
        return self._xnat_file_object.labels()

    @property
    def content_type(self) -> str:
        return self._xnat_file_object.content()

    @property
    def size(self) -> int:
        return int(self._xnat_file_object.size())

    @property
    def data(self) -> str:
        # Retrieve data to a temporary directory
        if self.exists():
            with TemporaryDirectory() as tempdir:
                return self._xnat_file_object.get_copy(tempdir + self.name)

        else:
            raise Exception("File data does not exist/ has been deleted.")

    # Check if file exists on XNAT server
    def exists(self) -> bool:
        return self._xnat_file_object.exists()

    def download(self, destination='') -> str:
        if destination == '':
            # If no download destination was given, download to a temporary directory (this is done in self.data)
            return self.data

        else:
            # Otherwise download file to given destination
            return self._xnat_file_object.get_copy(destination + self.name)

    # Delete file
    def delete_file(self) -> None:
        if self.exists():
            self._xnat_file_object.delete()

        else:
            raise Exception("File does not exist/has already been deleted.")


