from datetime import datetime
from typing import List, Optional

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB, ProjectData
from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, FailedDisconnectException,
    UnsuccessfulCreationException, UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat import XNAT


class Connection:
    """Handles the connection to PACS system and provides methods for interacting with projects, directories, and files."""
    
    this_timezone = timezone("Europe/Berlin")

    def __init__(self, server: str, username: str, password: str = '', session_id: str = '', kind: str = '') -> None:
        """
        Initializes the connection to the PACS server (accessible via _file_store_connection property).

        Args:
            server (str): The server address.
            username (str): The username for authentication.
            password (str, optional): The password for authentication. Defaults to ''.
            session_id (str, optional): The session ID for authentication. Defaults to ''.
            kind (str, optional): The type of connection (e.g., 'XNAT'). Defaults to ''.

        Raises:
            FailedConnectionException: If the connection type is unsupported or any exception occurs during connection initiation.
        """
        self.kind = kind
        self.server = server
        self.username = username
        self.password = password
        self.session_id = session_id
        self.cookies = None

        try:
            if self.kind == "XNAT":
                # Get valid XNAT session
                self._file_store_connection = XNAT(
                    server=server, username=username, password=password, session_id=session_id)
            else:
                # If kind is not "XNAT", raise an exception.
                msg = f"Unsupported connection type: {kind}"
                logger.exception(msg)
                raise FailedConnectionException
        except Exception as e:
            # If any exception occurs during connection initiation, log the exception and raise a FailedConnectionException.
            msg = f"Failed to establish the connection: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    @property
    def _kind(self) -> str:
        """
        Returns the kind of the connection.

        Returns:
            str: The kind of the connection. E.g.: 'XNAT'

        Raises:
            FailedConnectionException: If the connection type is unsupported.
        """
        if self.kind in ['XNAT']:
            return self.kind
        else:
            # If kind is not one of the supported connection types, raise a FailedConnectionException.
            msg = f"Unsupported connection type: {self.kind}"
            logger.exception(msg)
            raise FailedConnectionException

    @property
    def user(self) -> str:
        """
        Retrieves the user information.

        Returns:
            str: The username.

        Raises:
            FailedConnectionException: If the user information cannot be retrieved.
        """
        try:
            return self._file_store_connection.user
        except Exception as e:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            msg = f"Failed to retrieve user information: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException
    
    @property
    def all_users(self) -> list:
        """
        Retrieves all users from the connection.

        Returns:
            list: List of all users.

        Raises:
            FailedConnectionException: If the user information cannot be retrieved.
        """
        try:
            return self._file_store_connection.all_users
        except Exception as e:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            msg = f"Failed to retrieve user information: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __enter__(self) -> 'Connection':
        """
        Enters the context manager. Necessary along with __exit__ to support Context Management usage.

        Returns:
            Connection: The connection instance.

        Raises:
            FailedConnectionException: If unable to enter the context.
        """
        try:
            self._file_store_connection = self._file_store_connection.__enter__()
            return self
        except Exception as e:
            # Log the exception and raise a FailedConnectionException if unable to enter the context.
            msg = f"Failed to enter the context: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __exit__(self, type, value, traceback) -> None:
        """
        Exits the context manager.

        Args:
            type: The exception type.
            value: The exception value.
            traceback: The traceback object.

        Raises:
            FailedDisconnectException: If unable to exit the context.
        """
        try:
            self._file_store_connection.__exit__(type, value, traceback)
        except Exception as e:
            # Log the exception and raise a FailedDisconnectException if unable to exit the context.
            msg = f"Failed to exit the context: {str(e)}"
            logger.exception(msg)
            raise FailedDisconnectException

    def create_project(self, name: str, description: str = '', keywords: str = '', parameters: str = '') -> 'Project': # type: ignore
        """
        Creates a new project in the file store and database.

        Args:
            name (str): The name of the project.
            description (str, optional): The description of the project. Defaults to ''.
            keywords (str, optional): The keywords associated with the project. Defaults to ''.
            parameters (str, optional): Additional parameters for the project. Defaults to ''.

        Returns:
            Project: The created project instance.

        Raises:
            UnsuccessfulCreationException: If project creation fails.
        """
        from pacs2go.data_interface.pacs_data_interface import Project
        
        # Remove unallowed chars
        name = name.replace(".","")
        name = name.replace(",","")
        name = name.replace(";","")
        name = name.replace(":","")
        try:
            with self._file_store_connection as file_store:
                file_store_project = file_store.create_project(
                    name, description, keywords)
                
            with PACS_DB() as db:
                timestamp_now = datetime.now(
                    self.this_timezone).strftime("%Y-%m-%d %H:%M:%S")
                db.insert_into_project(ProjectData(name=name, keywords=keywords, description=description,
                                        parameters=parameters, timestamp_creation=timestamp_now, timestamp_last_updated=timestamp_now))
                
            logger.info(f"User {self.user} created a project: {name}")
            return Project(self, name, _project_file_store_object=file_store_project)
        
        except Exception as err:
            # Log the exception and raise an UnsuccessfulCreationException if project creation fails.
            msg = f"Failed to create the project: {str(err)} {str(name)}"
            logger.exception(msg)
            raise UnsuccessfulCreationException(f"{str(name)}")

    def get_project(self, name: str) -> Optional['Project']: # type: ignore
        """
        Retrieves a project by name.

        Args:
            name (str): The name of the project.

        Returns:
            Optional[Project]: The retrieved project instance.

        Raises:
            UnsuccessfulGetException: If the project cannot be retrieved.
        """
        from pacs2go.data_interface.pacs_data_interface import Project
        
        try:
            project = Project(self, name)
            logger.debug(f"User {self.user} retrieved information about project {project.name}.")
            return project
        except:
            msg = f"Failed to get Project '{name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Project '{name}'")

    def get_all_projects(self, only_accessible: bool = False) -> List['Project']:  # type: ignore  
        """
        Retrieves a list of all projects from the database.

        Args:
            only_accessible (bool, optional): If set to True, only projects which the user has rights to are retrieved. Defaults to False.

        Returns:
            List[Project]: List of Project objects.

        Raises:
            UnsuccessfulGetException: If unable to retrieve projects.
        """

        try:
            with PACS_DB() as db:
                pjs = db.get_all_projects()
                projects = [self.get_project(project.name) for project in pjs]
                if only_accessible:
                    projects = [p for p in projects if p.your_user_role != '']
            logger.debug(f"User {self.user} retrieved information about project list.")
            return projects
        except Exception:
            msg = "Failed to get all Projects"
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Projects")

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']: # type: ignore
        """
        Retrieves a directory by name from a specified project.

        Args:
            project_name (str): The name of the project.
            directory_name (str): The name of the directory.

        Returns:
            Optional[Directory]: The retrieved directory instance.

        Raises:
            UnsuccessfulGetException: If the directory cannot be retrieved.
        """
        from pacs2go.data_interface.pacs_data_interface import Directory
        
        try:
            d = Directory(self.get_project(project_name), directory_name)
            logger.debug(f"User {self.user} retrieved information about directory {d.unique_name}.")
            return d
        except Exception:
            msg = f"Failed to get Directory '{directory_name}' in Project '{project_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                f"Directory '{directory_name}'")

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']: # type: ignore
        from pacs2go.data_interface.pacs_data_interface import File
        """
        Retrieves a file by name from a specified directory in a project.

        Args:
            project_name (str): The name of the project.
            directory_name (str): The name of the directory.
            file_name (str): The name of the file.

        Returns:
            Optional[File]: The retrieved file instance.

        Raises:
            UnsuccessfulGetException: If the file cannot be retrieved.
        """
        try:
            f = File(directory=self.get_directory(
                project_name=project_name, directory_name=directory_name), name=file_name)
            return f
        except Exception:
            msg = f"Failed to get File '{file_name}' in Directory '{directory_name}' of Project '{project_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"File '{file_name}'")

    def get_favorites(self, username:str) -> List['Directory']: # type: ignore
        """
        Retrieves the list of favorited directories for a user.

        Args:
            username (str): The username whose favorites are to be retrieved.

        Returns:
            List[Directory]: List of favorited directories.

        Raises:
            UnsuccessfulGetException: If the favorites cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                favs = db.get_favorites_by_user(username)
            # Get directory objects
            favs = [self.get_directory(dir_data.unique_name.split(':')[0],
                dir_data.unique_name) for dir_data in favs]
            return favs
        except Exception:
                msg = f"Failed to get favorited directories for {username}."
                logger.exception(msg)
                raise UnsuccessfulGetException(f"favorites for {username}")