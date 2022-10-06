from typing import Optional, List, Any, Sequence, Union
from xnat_pacs_data_interface import XNAT, XNATProject


class Connection():
    def __init__(self, server:str, username: str, password: str, kind: str) -> None:
        self.kind = kind
        if self.kind == "XNAT":
            self.conn = XNAT(server, username, password)
        else:
            raise ValueError(kind)

    @property
    def user(self) -> str:
        if self.kind =="XNAT":
            return self.conn.user

    def __enter__(self) -> 'Connection':
        if self.kind =="XNAT":
            return self.conn.__enter__()

    def __exit__(self, type, value, traceback) -> None:
        if self.kind =="XNAT":
            return self.conn.__exit__(type, value, traceback)

    def get_project(self, name: str) -> Optional['Project']:
        if self.kind =="XNAT":
            self.conn.get_project(name)

    def get_all_projects(self) -> Sequence['Project']:
        if self.kind =="XNAT":
            self.conn.get_all_projects()


class Project():
    def __init__(self, connection: Connection, name: str) -> None:
        self.connection = connection
        self.name = name

    @property
    def description(self) -> str:
        pass

    @property
    def owners(self) -> List[str]:
        pass

    @property
    def your_user_role(self) -> str:
        pass

    def delete_project(self) -> None:
        pass

    # @abstractmethod
    # def get_directory(self, name) -> 'Directory':
    #     pass

    # @abstractmethod
    # def get_all_directories(self) -> Sequence['Directory']:
    #     pass

    # @abstractmethod
    # def insert(self, file_path: str) -> Union['Directory', 'File']:
    #     pass

"""
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
        pass """
