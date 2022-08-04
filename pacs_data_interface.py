from abc import ABC, abstractmethod, abstractproperty
from typing import Optional, List, Any, Sequence


class Connection(ABC):
    def __init__(self, username: Optional[str]='', password: Optional[str]='') -> None:
        self._projects = self.get_all_projects()
        self.interface: Any

    @abstractproperty
    def user(self) -> str:
        pass

    @abstractmethod
    def __enter__(self) -> 'Connection':
        pass

    @abstractmethod
    def __exit__(self, type, value, traceback) -> None:
        pass

    @abstractmethod
    def get_project(self, name: str) -> Optional['Project']:
        pass

    @abstractmethod
    def get_all_projects(self) -> Sequence['Project']:
        pass


class Project(ABC):
    def __init__(self, connection: Connection, name: str) -> None:
        self.connection = connection
        self.name = name

    @abstractproperty
    def description(self) -> str:
        pass

    @abstractproperty
    def owners(self) -> List[str]:
        pass

    @abstractproperty
    def your_user_role(self) -> str:
        pass

    @abstractmethod
    def delete_project(self) -> None:
        pass

    @abstractmethod
    def get_directory(self, name) -> 'Directory':
        pass

    @abstractmethod
    def get_all_directories(self) -> Sequence['Directory']:
        pass

    @abstractmethod
    def insert_zip_into_project(self, file_path: str) -> 'Directory':
        pass

    @abstractmethod
    def insert_file_into_project(self, file_path: str) -> 'File':
        pass


class Directory(ABC):
    def __init__(self, project: Project, name: str) -> None:
        self.name = name
        self.project = project

    @abstractmethod
    def delete_directory(self) -> None:
        pass

    @abstractmethod
    def get_file(self, file_name: str) -> 'File':
        pass

    @abstractmethod
    def get_all_files(self) -> Sequence['File']:
        pass


class File(ABC):
    def __init__(self, directory: Directory, name: str) -> None:
        self.directory = directory
        self.name = name

    @abstractproperty
    def format(self) -> str:
        pass

    @abstractproperty
    def size(self) -> int:
        pass

    @abstractproperty
    def data(self) -> str:
        pass

    @abstractmethod
    def delete_file(self) -> None:
        pass
