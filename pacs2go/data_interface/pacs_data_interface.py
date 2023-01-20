from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

from pacs2go.data_interface.xnat_pacs_data_interface import pyXNAT
from pacs2go.data_interface.xnat_pacs_data_interface import pyXNATDirectory
from pacs2go.data_interface.xnat_pacs_data_interface import pyXNATFile
from pacs2go.data_interface.xnat_pacs_data_interface import pyXNATProject

from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNAT
from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNATDirectory
from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNATFile
from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNATProject


class Connection():
    def __init__(self, server: str, username: str, password: str = None, session_id: str = None, kind: str = None) -> None:
        self.kind = kind
        self.server = server
        self.username = username
        self.password = password
        self.session_id = session_id
        self.cookies = None

        if self.kind == "pyXNAT":
            self._xnat_connection = pyXNAT(server, username, password)
        elif self.kind == "XNAT":
            self._xnat_connection = XNAT(server=server, username=username, password=password, session_id=session_id)
        else:
            raise ValueError(kind)

    @property
    def _kind(self) -> str:
        return self.kind

    @property
    def user(self) -> str:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.user
        else:
            raise ValueError(self.kind)

    def __enter__(self) -> 'Connection':
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.__enter__()

    def __exit__(self, type, value, traceback) -> None:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.__exit__(type, value, traceback)
        else:
            raise ValueError(self.kind)

    def create_project(self, name) -> Optional['Project']:
        if self.kind == "XNAT":
            return self._xnat_connection.create_project(name)
        else:
            raise ValueError(self.kind)

    def get_project(self, name: str) -> Optional['Project']:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.get_project(name)
        else:
            raise ValueError(self.kind)

    def get_all_projects(self) -> List['Project']:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.get_all_projects()
        else:
            raise ValueError(self.kind)

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.get_directory(project_name, directory_name)
        else:
            raise ValueError(self.kind)

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
        if self.kind == "pyXNAT" or self.kind == "XNAT":
            return self._xnat_connection.get_file(
                project_name, directory_name, file_name)
        else:
            raise ValueError(self.kind)


class Project():
    def __init__(self, connection: Connection, name: str) -> None:
        self.connection = connection
        self.name = name
        if self.connection._kind == "pyXNAT":
            self._xnat_project = pyXNATProject(connection, name)
        elif self.connection._kind == "XNAT":
            self._xnat_project = XNATProject(connection,name)
        else:
            raise ValueError(self.connection._kind)

    @property
    def description(self) -> str:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.description
        else:
            raise ValueError(self.connection._kind)

    def set_description(self, description_string: str) -> None:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.set_description(description_string)
        else:
            raise ValueError(self.connection._kind)

    @property
    def keywords(self) -> str:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.keywords
        else:
            raise ValueError(self.connection._kind)

    def set_keywords(self, keywords_string: str) -> None:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.set_keywords(keywords_string)
        else:
            raise ValueError(self.connection._kind)

    @property
    def owners(self) -> List[str]:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.owners
        else:
            raise ValueError(self.connection._kind)

    @property
    def your_user_role(self) -> str:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.your_user_role
        else:
            raise ValueError(self.connection._kind)

    def exists(self) -> bool:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.exists()
        else:
            raise ValueError(self.connection._kind)

    def download(self, destination: str) -> str:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.download(destination)
        else:
            raise ValueError(self.connection._kind)

    def delete_project(self) -> None:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.delete_project()
        else:
            raise ValueError(self.connection._kind)

    def get_directory(self, name) -> 'Directory':
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.get_directory(name)
        else:
            raise ValueError(self.connection._kind)

    def get_all_directories(self) -> Sequence['Directory']:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.get_all_directories()
        else:
            raise ValueError(self.connection._kind)

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['Directory', 'File']:
        if self.connection._kind == "pyXNAT" or self.connection._kind == "XNAT":
            return self._xnat_project.insert(file_path, directory_name, tags_string)
        else:
            raise ValueError(self.connection._kind)


class Directory():
    def __init__(self, project: Project, name: str) -> None:
        self.name = name
        self.project = project
        if self.project.connection._kind == "pyXNAT":
            self._xnat_directory = pyXNATDirectory(project, name)
        elif self.project.connection._kind == "XNAT":
            self._xnat_project = XNATDirectory(project,name)
        else:
            raise ValueError(self.project.connection._kind)

    @property
    def contained_file_tags(self) -> str:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.contained_file_tags
        else:
            raise ValueError(self.connection._kind)

    @property
    def number_of_files(self) -> str:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.number_of_files
        else:
            raise ValueError(self.project.connection._kind)

    def exists(self) -> bool:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.exists()
        else:
            raise ValueError(self.project.connection._kind)

    def delete_directory(self) -> None:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.delete_directory()
        else:
            raise ValueError(self.project.connection._kind)

    def get_file(self, file_name: str) -> 'File':
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.get_file(file_name)
        else:
            raise ValueError(self.project.connection._kind)

    def get_all_files(self) -> List['File']:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.get_all_files()
        else:
            raise ValueError(self.project.connection._kind)

    def download(self, destination: str) -> str:
        if self.project.connection._kind == "pyXNAT" or self.project.connection._kind == "XNAT":
            return self._xnat_directory.download(destination)
        else:
            raise ValueError(self.connection._kind)


class File():
    def __init__(self, directory: Directory, name: str) -> None:
        self.directory = directory
        self.name = name
        if self.directory.project.connection._kind == "pyXNAT":
            self._xnat_file = pyXNATFile(directory, name)
        if self.directory.project.connection._kind == "XNAT":
            self._xnat_file = XNATFile(directory, name)
        else:
            raise ValueError(self.directory.project.connection._kind)

    @property
    def format(self) -> str:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.format
        else:
            raise ValueError(self.directory.project.connection._kind)

    @property
    def content_type(self) -> str:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.content_type
        else:
            raise ValueError(self.directory.project.connection._kind)

    @property
    def tags(self) -> str:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.tags
        else:
            raise ValueError(self.directory.project.connection._kind)

    @property
    def size(self) -> int:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.size
        else:
            raise ValueError(self.directory.project.connection._kind)

    @property
    def data(self) -> str:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.data
        else:
            raise ValueError(self.directory.project.connection._kind)

    def exists(self) -> bool:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.exists()
        else:
            raise ValueError(self.connection._kind)

    def download(self, destination: str = '') -> str:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.download()
        else:
            raise ValueError(self.connection._kind)

    def delete_file(self) -> None:
        if self.directory.project.connection._kind == "pyXNAT" or self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.delete_file()
        else:
            raise ValueError(self.directory.project.connection._kind)
