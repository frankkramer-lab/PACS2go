from abc import ABC, abstractmethod, abstractproperty

class Connection(ABC):
        def __init__(self, username, password):
                self._projects = self.get_all_projects()

        @abstractmethod
        def __enter__(self):
                pass

        @abstractmethod
        def __exit__(self, type, value, traceback):
                pass

        @abstractmethod
        def get_project(self, name):
                pass

        @abstractmethod
        def get_all_projects(self):
                pass
        


class Project(ABC):
        def __init__(self, connection, name):
                self.connection = connection
                self.name = name
                self._directories = self.get_all_directories()

        @abstractproperty
        def description(self):
                pass

        @abstractproperty
        def owners(self):
                pass

        @abstractproperty
        def your_user_role(self):
                pass

        @abstractmethod
        def delete_project(self):
                pass

        @abstractmethod
        def get_directory(self, name):
                pass

        @abstractmethod
        def get_all_directories(self):
                pass

        @abstractmethod
        def insert_zip_into_project(self, file_path):
                pass
        
        def insert_file_into_project(self, file_path):
                pass
        

class Directory(ABC):
        def __init__(self, project, name):
                self.name = name
                self.project = project
                self._files = self.get_all_files()

        @abstractmethod
        def delete_directory(self):
                pass

        @abstractmethod
        def get_file(self, file_name):
                pass

        @abstractmethod
        def get_all_files(self):
                pass

class File(ABC):
        def __init__(self,directory,name):
                self.directory = directory
                self.name = name

        @abstractproperty
        def format(self):
                pass

        @abstractproperty
        def size(self):
                pass

        @abstractproperty
        def data(self):
                pass

        @abstractmethod
        def delete_file(self):
                pass