from typing import Optional, List, Any, Sequence, Union
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT, XNATDirectory, XNATFile, XNATProject


class Connection():
    def __init__(self, server: str, username: str, password: str, kind: str) -> None:
        self.kind = kind
        if self.kind == "XNAT":
            self._xnat_connection = XNAT(server, username, password)
        else:
            raise ValueError(kind)

    @property
    def _kind(self) -> str:
        return self.kind

    @property
    def user(self) -> str:
        if self.kind == "XNAT":
            return self._xnat_connection.user
        else:
            raise ValueError(self.kind)

    def __enter__(self) -> 'Connection':
        if self.kind == "XNAT":
            return self._xnat_connection.__enter__()

    def __exit__(self, type, value, traceback) -> None:
        if self.kind == "XNAT":
            return self._xnat_connection.__exit__(type, value, traceback)
        else:
            raise ValueError(self.kind)

    def get_project(self, name: str) -> Optional['Project']:
        if self.kind == "XNAT":
            self._xnat_connection.get_project(name)
        else:
            raise ValueError(self.kind)

    def get_all_projects(self) -> Sequence['Project']:
        if self.kind == "XNAT":
            self._xnat_connection.get_all_projects()
        else:
            raise ValueError(self.kind)


class Project():
    def __init__(self, connection: Connection, name: str) -> None:
        self.connection = connection
        self.name = name
        if self.connection._kind == "XNAT":
            self._xnat_project = XNATProject(connection, name)
        else:
            return ValueError(self.connection._kind)

    @property
    def description(self) -> str:
        if self.connection._kind == "XNAT":
            return self._xnat_project.description
        else:
            return ValueError(self.connection._kind)

    @property
    def owners(self) -> List[str]:
        if self.connection._kind == "XNAT":
            return self._xnat_project.owners
        else:
            return ValueError(self.connection._kind)

    @property
    def your_user_role(self) -> str:
        if self.connection._kind == "XNAT":
            return self._xnat_project.your_user_role
        else:
            return ValueError(self.connection._kind)

    def delete_project(self) -> None:
        if self.connection._kind == "XNAT":
            return self._xnat_project.delete_project()
        else:
            return ValueError(self.connection._kind)

    def get_directory(self, name) -> 'Directory':
        if self.connection._kind == "XNAT":
            return self._xnat_project.get_directory(name)
        else:
            return ValueError(self.connection._kind)

    def get_all_directories(self) -> Sequence['Directory']:
        if self.connection._kind == "XNAT":
            return self._xnat_project.get_all_directories()
        else:
            return ValueError(self.connection._kind)

    def insert(self, file_path: str, directory_name: str = '') -> Union['Directory', 'File']:
        if self.connection._kind == "XNAT":
            return self._xnat_project.insert(file_path, directory_name)
        else:
            return ValueError(self.connection._kind)


class Directory():
    def __init__(self, project: Project, name: str) -> None:
        self.name = name
        self.project = project
        if self.project.connection._kind == "XNAT":
            self._xnat_directory = XNATDirectory(project, name)
        else:
            return ValueError(self.project.connection._kind)

    def delete_directory(self) -> None:
        if self.project.connection._kind == "XNAT":
            return self._xnat_directory.delete_directory()
        else:
            return ValueError(self.project.connection._kind)

    def get_file(self, file_name: str) -> 'File':
        if self.project.connection._kind == "XNAT":
            return self._xnat_directory.get_file(file_name)
        else:
            return ValueError(self.project.connection._kind)

    def get_all_files(self) -> Sequence['File']:
        if self.project.connection._kind == "XNAT":
            return self._xnat_directory.get_all_files()
        else:
            return ValueError(self.project.connection._kind)


class File():
    def __init__(self, directory: Directory, name: str) -> None:
        self.directory = directory
        self.name = name
        if self.directory.project.connection._kind == "XNAT":
            self._xnat_file = XNATFile(directory, name)
        else:
            return ValueError(self.directory.project.connection._kind)

    @property
    def format(self) -> str:
        if self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.format
        else:
            return ValueError(self.directory.project.connection._kind)

    @property
    def size(self) -> int:
        if self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.size
        else:
            return ValueError(self.directory.project.connection._kind)

    @property
    def data(self) -> str:
        if self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.data
        else:
            return ValueError(self.directory.project.connection._kind)

    def delete_file(self) -> None:
        if self.directory.project.connection._kind == "XNAT":
            return self._xnat_file.delete_file()
        else:
            return ValueError(self.directory.project.connection._kind) 
