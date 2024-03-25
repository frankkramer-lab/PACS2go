from datetime import datetime
from typing import List, Optional

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB, ProjectData
from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, FailedDisconnectException,
    UnsuccessfulCreationException, UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.pacs_data_interface.directory import Directory
from pacs2go.data_interface.pacs_data_interface.file import File
from pacs2go.data_interface.pacs_data_interface.project import Project
from pacs2go.data_interface.xnat_rest_wrapper import XNAT


class Connection:
    this_timezone = timezone("Europe/Berlin")

    def __init__(self, server: str, username: str, password: str = '', session_id: str = '', kind: str = '', db_host: str = 'data-structure-db', db_port: int = 5432) -> None:
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
        if self.kind in ['XNAT']:
            return self.kind
        else:
            # If kind is not one of the supported connection types, raise a FailedConnectionException.
            msg = f"Unsupported connection type: {self.kind}"
            logger.exception(msg)
            raise FailedConnectionException

    @property
    def user(self) -> str:
        try:
            return self._file_store_connection.user
        except Exception as e:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            msg = f"Failed to retrieve user information: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException
    
    @property
    def all_users(self) -> list:
        try:
            return self._file_store_connection.all_users
        except Exception as e:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            msg = f"Failed to retrieve user information: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __enter__(self) -> 'Connection':
        try:
            self._file_store_connection = self._file_store_connection.__enter__()
            return self
        except Exception as e:
            # Log the exception and raise a FailedConnectionException if unable to enter the context.
            msg = f"Failed to enter the context: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __exit__(self, type, value, traceback) -> None:
        try:
            self._file_store_connection.__exit__(type, value, traceback)
        except Exception as e:
            # Log the exception and raise a FailedDisconnectException if unable to exit the context.
            msg = f"Failed to exit the context: {str(e)}"
            logger.exception(msg)
            raise FailedDisconnectException

    def create_project(self, name: str, description: str = '', keywords: str = '', parameters: str = '') -> 'Project':
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

    def get_project(self, name: str) -> Optional['Project']:
        try:
            project = Project(self, name)
            logger.debug(f"User {self.user} retrieved information about project {project.name}.")
            return project
        except:
            msg = f"Failed to get Project '{name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Project '{name}'")
        
    #p.your_user_role != '' or current_user.id=='admin'

    def get_all_projects(self, only_accessible:bool = False) -> List['Project']:    
        """Retrieves a list of all projects from DB
        
        Args:
            only_accessible (boolean): if set to True then only projects which the user has rights to are retrieved

        Raises:
            UnsuccessfulGetException

        Returns:
            List['Project']: List of Project objects
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

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
        try:
            d = Directory(self.get_project(project_name), directory_name)
            logger.debug(f"User {self.user} retrieved information about directory {d.unique_name}.")
            return d
        except Exception:
            msg = f"Failed to get Directory '{directory_name}' in Project '{project_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                f"Directory '{directory_name}'")

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
        try:
            f = File(directory=self.get_directory(
                project_name=project_name, directory_name=directory_name), name=file_name)
            return f
        except Exception:
            msg = f"Failed to get File '{file_name}' in Directory '{directory_name}' of Project '{project_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"File '{file_name}'")

    def get_favorites(self, username:str) -> List['Directory']:
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