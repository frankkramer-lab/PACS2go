from pacs2go.data_interface.exceptions.exceptions import DownloadException
from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import FailedDisconnectException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulAttributeUpdateException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulDeletionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulGetException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulProjectCreationException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulUploadException
from pacs2go.data_interface.exceptions.exceptions import WrongUploadFormatException
from pacs2go.data_interface.data_structure_db import PACS_DB
from pacs2go.data_interface.data_structure_db import ProjectData
from pacs2go.data_interface.data_structure_db import DirectoryData
from pacs2go.data_interface.data_structure_db import FileData
from pacs2go.data_interface.xnat_rest_wrapper import XNAT
from pacs2go.data_interface.xnat_rest_wrapper import XNATDirectory
from pacs2go.data_interface.xnat_rest_wrapper import XNATFile
from pacs2go.data_interface.xnat_rest_wrapper import XNATProject
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

import os
import zipfile


class Connection():
    def __init__(self, server: str, username: str, password: str = '', session_id: str = '', kind: str = '') -> None:
        self.kind = kind
        self.server = server
        self.username = username
        self.password = password
        self.session_id = session_id
        self.cookies = None

        try:
            if self.kind == "XNAT":
                self._xnat_connection = XNAT(
                    server=server, username=username, password=password, session_id=session_id)
            else:
                raise ValueError(kind)
        except:
            raise FailedConnectionException

    @property
    def _kind(self) -> str:
        if self.kind in ['XNAT']:
            return self.kind
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def user(self) -> str:
        try:
            return self._xnat_connection.user
        except:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            raise FailedConnectionException

    def __enter__(self) -> 'Connection':
        return self._xnat_connection.__enter__()

    def __exit__(self, type, value, traceback) -> None:
        try:
            return self._xnat_connection.__exit__(type, value, traceback)
        except:
            raise FailedDisconnectException

    def create_project(self, name: str, description: str = '', keywords: str = '') -> 'Project':
        try:
            with PACS_DB() as db:
                db.insert_into_project(ProjectData(name=name))
            return self._xnat_connection.create_project(name, description, keywords)
        except:
            raise UnsuccessfulProjectCreationException(str(name))

    def get_project(self, name: str) -> Optional['Project']:
        try:
            return self._xnat_connection.get_project(name)
        except:
            raise UnsuccessfulGetException(f"Project '{name}'")

    def get_all_projects(self) -> List['Project']:
        try:
            return self._xnat_connection.get_all_projects()
        except:
            raise UnsuccessfulGetException("Projects")

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
        try:
            return self._xnat_connection.get_directory(project_name, directory_name)
        except:
            raise UnsuccessfulGetException(f"Directory '{directory_name}'")

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
        try:
            return self._xnat_connection.get_file(
                project_name, directory_name, file_name)
        except:
            raise UnsuccessfulGetException(f"File '{file_name}'")


class Project():
    def __init__(self, connection: Connection, name: str) -> None:
        self.connection = connection
        self.name = name

        if self.connection._kind == "XNAT":
            try:
                self._xnat_project = XNATProject(connection, name)
            except:
                raise UnsuccessfulGetException(f"Project '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def description(self) -> str:
        try:
            return self._xnat_project.description
        except:
            raise UnsuccessfulGetException("Project description")

    def set_description(self, description_string: str) -> None:
        try:
            return self._xnat_project.set_description(description_string)
        except:
            raise UnsuccessfulAttributeUpdateException(
                f"a new description ('{description_string}')")

    @property
    def keywords(self) -> str:
        try:
            return self._xnat_project.keywords
        except:
            raise UnsuccessfulGetException("Project-related keywords")

    def set_keywords(self, keywords_string: str) -> None:
        try:
            return self._xnat_project.set_keywords(keywords_string)
        except:
            raise UnsuccessfulAttributeUpdateException(
                f"the project keywords to '{keywords_string}'")

    @property
    def owners(self) -> List[str]:
        try:
            return self._xnat_project.owners
        except:
            raise UnsuccessfulGetException(
                "Project users that are assigned an 'owner' role")

    @property
    def your_user_role(self) -> str:
        try:
            return self._xnat_project.your_user_role
        except:
            raise UnsuccessfulGetException("Your user role")

    def exists(self) -> bool:
        return self._xnat_project.exists()

    def download(self, destination: str) -> str:
        try:
            return self._xnat_project.download(destination)
        except:
            raise DownloadException

    def delete_project(self) -> None:
        try:
            with PACS_DB() as db:
                db.delete_project_by_name(self.name)
            return self._xnat_project.delete_project()
        except:
            raise UnsuccessfulDeletionException(f"Project '{self.name}'")

    def get_directory(self, name) -> 'Directory':
        try:
            return self._xnat_project.get_directory(name)
        except:
            raise UnsuccessfulGetException(f"Directory '{name}'")

    def get_all_directories(self) -> Sequence['Directory']:
        try:
            directories_from_xnat = self._xnat_project.get_all_directories()
            with PACS_DB() as db:
                directories_from_db = db.get_directories_by_project(self.name)

            # only return the directories that live directly under the project (no sub-dirs)
            filtered_directories = [dir_xnat for dir_xnat in directories_from_xnat
                                    if any(dir_xnat.name == dir_data.unique_name for dir_data in directories_from_db)
                                    ]

            return filtered_directories

        except:
            raise UnsuccessfulGetException("Directories")

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['Directory', 'File']:
        try:
            # File path leads to a single file
            if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
                # TODO: directory name has to be unique -> create unique dir name before hand
                file = self._xnat_project.insert_file_into_project(file_path, directory_name, tags_string)
                with PACS_DB() as db:
                    # TODO: if directory does not exist insert directory
                    db.insert_into_file(FileData(file_name=file.name, parent_directory=file.directory))
                return file
            
            # File path equals a zip file
            elif zipfile.is_zipfile(file_path):
                directory = self._xnat_project.insert_zip_into_project(file_path, directory_name, tags_string)
                with PACS_DB() as db:
                    # TODO: differentiate between subdir and high-level dir, create unique name from parents and display name
                    db.insert_into_directory(DirectoryData(unique_name='', name=directory.name, dir_name='', project_name = ''))
                    # TODO: insert all files into db
                return directory
            
            else:
                raise ValueError
        except ValueError:
            raise WrongUploadFormatException(str(file_path))
        except:
            raise UnsuccessfulUploadException(str(file_path))


class Directory():
    def __init__(self, project: Project, name: str) -> None:
        self.name = name
        self.project = project

        if self.project.connection._kind == "XNAT":
            try:
                self._xnat_directory = XNATDirectory(project, name)
            except:
                raise UnsuccessfulGetException(f"Directory '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def contained_file_tags(self) -> str:
        try:
            return self._xnat_directory.contained_file_tags
        except:
            raise UnsuccessfulGetException("File tags")

    @property
    def number_of_files(self) -> str:
        try:
            return self._xnat_directory.number_of_files
        except:
            raise UnsuccessfulGetException("Number of files in this directory")

    def exists(self) -> bool:
        return self._xnat_directory.exists()

    def delete_directory(self) -> None:
        try:
            for subdir in self.get_subdirectories():
                subdir.delete_directory()
            with PACS_DB() as db:
                db.delete_directory_by_name(self.name)
            return self._xnat_directory.delete_directory()
        except:
            raise UnsuccessfulDeletionException(f"directory '{self.name}'")
        
    def get_subdirectories(self) -> List['Directory']:
        with PACS_DB() as db:
            subdirectories_from_db = db.get_subdirectories_by_directory(self.name)
        directories_from_xnat = self._xnat_project.get_all_directories()

        # only return the directories that are subdirectories of this directory
        filtered_directories = [dir_xnat for dir_xnat in directories_from_xnat
                                if any(dir_xnat.name == dir_data.unique_name for dir_data in subdirectories_from_db)
                                ]

        return filtered_directories


    def get_file(self, file_name: str) -> 'File':
        try:
            return self._xnat_directory.get_file(file_name)
        except:
            raise UnsuccessfulGetException(f"File '{file_name}'")

    def get_all_files(self) -> List['File']:
        try:
            return self._xnat_directory.get_all_files()
        except:
            raise UnsuccessfulGetException("Files")

    def download(self, destination: str) -> str:
        try:
            return self._xnat_directory.download(destination)
        except:
            raise DownloadException


class File():
    def __init__(self, directory: Directory, name: str) -> None:
        self.directory = directory
        self.name = name

        if self.directory.project.connection._kind == "XNAT":
            try:
                self._xnat_file = XNATFile(directory, name)
            except:
                raise UnsuccessfulGetException(f"File '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def format(self) -> str:
        try:
            return self._xnat_file.format
        except:
            raise UnsuccessfulGetException("File format")

    @property
    def content_type(self) -> str:
        try:
            return self._xnat_file.content_type
        except:
            raise UnsuccessfulGetException("File content type")

    @property
    def tags(self) -> str:
        try:
            return self._xnat_file.tags
        except:
            raise UnsuccessfulGetException("File tags")

    @property
    def size(self) -> int:
        try:
            return self._xnat_file.size
        except:
            raise UnsuccessfulGetException("File size")

    @property
    def data(self) -> bytes:
        try:
            return self._xnat_file.data
        except:
            raise UnsuccessfulGetException("The actual file data itself")

    def exists(self) -> bool:
        return self._xnat_file.exists()

    def download(self, destination: str = '') -> str:
        try:
            return self._xnat_file.download(destination)
        except:
            raise DownloadException

    def delete_file(self) -> None:
        try:
            with PACS_DB() as db:
                db.delete_file_by_name(self.name)
            return self._xnat_file.delete_file()
        except:
            raise UnsuccessfulDeletionException(f"file '{self.name}'")
