import datetime
import tempfile
from pacs2go.data_interface.exceptions.exceptions import DownloadException
from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import FailedDisconnectException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulAttributeUpdateException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulDeletionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulGetException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulCreationException
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
    def __init__(self, server: str, username: str, password: str = '', session_id: str = '', kind: str = '', db_host: str = 'data-structure-db', db_port: int = 5432) -> None:
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
        self._xnat_connection = self._xnat_connection.__enter__()
        return self

    def __exit__(self, type, value, traceback) -> None:
        try:
            self._xnat_connection.__exit__(type, value, traceback)
        except:
            raise FailedDisconnectException

    def create_project(self, name: str, description: str = '', keywords: str = '') -> 'Project':
        try:
            p = self.get_project(name)
            return p
        except UnsuccessfulGetException as err:
            try:
                with self._xnat_connection as xnat:
                    xnat_project = xnat.create_project(
                        name, description, keywords)
                with PACS_DB() as db:
                    db.insert_into_project(ProjectData(name=name))
                return Project(self, name, _project_filestorage_object=xnat_project)
            except Exception as err:
                raise UnsuccessfulCreationException(f"{err} {str(name)}")

    def get_project(self, name: str) -> Optional['Project']:
        try:
            return Project(self, name)
        except:
            raise UnsuccessfulGetException(f"Project '{name}'")

    def get_all_projects(self) -> List['Project']:
        try:
            with PACS_DB() as db:
                pjs = db.get_all_projects()
            projects = [self.get_project(project) for project in pjs]
            return projects
        except Exception as err:
            raise UnsuccessfulGetException(f"{err} Projects")

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
        try:
            return Directory(self.get_project(project_name), directory_name)
        except Exception as err:
            raise UnsuccessfulGetException(
                f"Directory '{directory_name}' {err}")

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
        try:
            return File(directory=self.get_directory(project_name=project_name, directory_name=directory_name), name=file_name)
        except Exception as err:
            raise UnsuccessfulGetException(f"File '{file_name}' {err}")


class Project():
    def __init__(self, connection: Connection, name: str, _project_filestorage_object=None) -> None:
        self.connection = connection
        self.name = name

        if _project_filestorage_object:
            self._xnat_project = _project_filestorage_object
        elif self.connection._kind == "XNAT":
            try:
                self._xnat_project = XNATProject(
                    connection._xnat_connection, name)
            except Exception as err:
                raise UnsuccessfulGetException(f"Projectx '{name}'")
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
            self._xnat_project.delete_project()
        except:
            raise UnsuccessfulDeletionException(f"Project '{self.name}'")

    def create_directory(self, name: str) -> 'Directory':
        try:
            d = self.get_directory(name)
            return d
        except:
            try:
                with PACS_DB() as db:
                    unique_name = self.name + '::' + name
                    db.insert_into_directory(DirectoryData(
                        unique_name=unique_name, dir_name=name, parent_project=self.name, parent_directory=None))

                dir = self._xnat_project.create_directory(unique_name)
                return Directory(project=self, name=unique_name, _directory_filestorage_object=dir)
            except Exception as err:
                raise UnsuccessfulCreationException(str(name))

    def get_directory(self, name, _directory_filestorage_object=None) -> 'Directory':
        try:
            return Directory(self, name=name, _directory_filestorage_object=_directory_filestorage_object)
        except:
            raise UnsuccessfulGetException(f"Directory '{name}'")

    def get_all_directories(self) -> Sequence['Directory']:
        try:
            with PACS_DB() as db:
                directories_from_db = db.get_directories_by_project(self.name)

            # Get directory objects
            filtered_directories = [self.get_directory(
                dir_data.unique_name) for dir_data in directories_from_db]

            return filtered_directories

        except:
            raise UnsuccessfulGetException("Directories")

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['Directory', 'File']:
        try:
            if directory_name == '':
                if zipfile.is_zipfile(file_path):
                    # get the name of the zipfile
                    directory_name = file_path.rsplit(
                        "/", 1)[-1].rsplit(".", 1)[0]
                else:
                    # No desired name was given, set the name as the current timestamp
                    directory_name = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

            if directory_name.count('::') == 1 or directory_name.count('::') == 0:
                # Name is not an inherited name and is directly under a project, create/get directory
                directory = self.create_directory(directory_name)
            else:
                # Get the parent directory of what is a subdirectory (contains a -) by its unique name
                parent_dir = self.get_directory(
                    directory_name.rsplit('::', 1)[0])

                # Create/get the subdirectory from parent directory
                directory = parent_dir.create_subdirectory(
                    directory_name.rsplit('::', 1)[-1])

            # File path leads to a single file
            if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
                file = self._xnat_project.insert_file_into_project(
                    file_path, directory.name, tags_string)

                with PACS_DB() as db:
                    db.insert_into_file(
                        FileData(file_name=file.name, parent_directory=directory.name))
                return File(directory=directory, name=file.name, _file_filestorage_object=file)

            # File path equals a zip file
            elif zipfile.is_zipfile(file_path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Unzip the file to the temporary directory
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    root_dir = directory

                    # Walk through the unzipped directory
                    for root, dirs, files in os.walk(temp_dir):
                        if root == temp_dir:
                            # Skip tempdir name
                            continue
                        if os.path.basename(root) == root_dir.display_name:
                            # First level directory is already created
                            current_dir = root_dir
                        else:
                            # Create sub-directory according to zipfile
                            current_dir = directory.create_subdirectory(
                                os.path.basename(root))
    
                        for file_name in files:
                            # Insert files of current level to current directory
                            self._xnat_project.insert_file_into_project(
                                os.path.join(root, file_name), current_dir.name, tags_string)
                        directory = current_dir
                    return root_dir

            else:
                raise ValueError
        except ValueError:
            raise WrongUploadFormatException(str(file_path.split("-")[-1]))
        except Exception as err:
            raise UnsuccessfulUploadException(str(file_path.split("-")[-1]))


class Directory():
    def __init__(self, project: Project, name: str, _directory_filestorage_object=None) -> None:
        self.name = name  # unique
        self.display_name = self.name.split('::')[-1]
        self.project = project

        if _directory_filestorage_object:
            self._xnat_directory = _directory_filestorage_object
        elif self.project.connection._kind == "XNAT":
            try:
                self._xnat_directory = XNATDirectory(
                    project._xnat_project, name)
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

    @property
    def parent_directory_name(self) -> 'str':
        try:
            with PACS_DB() as db:
                return db.get_directory_by_name(self.name).parent_directory
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

        except:
            raise UnsuccessfulDeletionException(f"directory '{self.name}'")

    def create_subdirectory(self, name: str) -> 'Directory':
        try:
            d = self.project.get_directory(self.name + '::' + name)
            return d
        except:
            try:
                with PACS_DB() as db:
                    unique_name = self.name + '::' + name
                    db.insert_into_directory(DirectoryData(
                        unique_name=unique_name, dir_name=name, parent_project=None, parent_directory=self.name))

                dir = self.project._xnat_project.create_directory(unique_name)
                return Directory(project=self.project, name=unique_name, _directory_filestorage_object=dir)
            except Exception as err:
                raise UnsuccessfulCreationException(str(name))

    def get_subdirectories(self) -> List['Directory']:
        with PACS_DB() as db:
            subdirectories_from_db = db.get_subdirectories_by_directory(
                self.name)

        # Only return the directories that are subdirectories of this directory
        filtered_directories = [
            Directory(self.project, d.unique_name) for d in subdirectories_from_db]

        return filtered_directories

    def get_file(self, file_name: str, _file_filestorage_object=None) -> 'File':
        try:
            return File(self, name=file_name, _file_filestorage_object=_file_filestorage_object)
        except:
            raise UnsuccessfulGetException(f"File '{file_name}'")

    def get_all_files(self) -> List['File']:
        try:
            fs = self._xnat_directory.get_all_files()
            files = [self.get_file(
                file_name=f.name, _file_filestorage_object=f) for f in fs]
            return files
        except Exception as err:
            raise UnsuccessfulGetException("Files")

    def download(self, destination: str) -> str:
        try:
            return self._xnat_directory.download(destination)
        except:
            raise DownloadException


class File():
    def __init__(self, directory: Directory, name: str, _file_filestorage_object=None) -> None:
        self.directory = directory
        self.name = name

        if _file_filestorage_object:
            self._xnat_file = _file_filestorage_object
        if self.directory.project.connection._kind == "XNAT":
            try:
                self._xnat_file = XNATFile(directory._xnat_directory, name)
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
            self._xnat_file.delete_file()

            with PACS_DB() as db:
                db.delete_file_by_name(self.name)

        except:
            raise UnsuccessfulDeletionException(f"file '{self.name}'")
