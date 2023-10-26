import logging
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Sequence, Union

from pytz import timezone

from pacs2go.data_interface.data_structure_db import (PACS_DB, CitationData,
                                                      DirectoryData, FileData,
                                                      ProjectData)
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException, FailedDisconnectException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulCreationException,
    UnsuccessfulDeletionException, UnsuccessfulGetException,
    UnsuccessfulUploadException, WrongUploadFormatException)
from pacs2go.data_interface.xnat_rest_wrapper import (XNAT, XNATDirectory,
                                                      XNATFile, XNATProject)
from pacs2go.data_interface.logs.config_logging import data_interface_logger

# Init logger
logger = data_interface_logger()
# File format metadata
file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI',
               '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT'}

timezone = timezone("Europe/Berlin")


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
            return self._xnat_connection.user
        except Exception as e:
            # FailedConnectionException because if this information can not be retrieved the connection is corrupted
            msg = f"Failed to retrieve user information: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __enter__(self) -> 'Connection':
        try:
            self._xnat_connection = self._xnat_connection.__enter__()
            return self
        except Exception as e:
            # Log the exception and raise a FailedConnectionException if unable to enter the context.
            msg = f"Failed to enter the context: {str(e)}"
            logger.exception(msg)
            raise FailedConnectionException

    def __exit__(self, type, value, traceback) -> None:
        try:
            self._xnat_connection.__exit__(type, value, traceback)
        except Exception as e:
            # Log the exception and raise a FailedDisconnectException if unable to exit the context.
            msg = f"Failed to exit the context: {str(e)}"
            logger.exception(msg)
            raise FailedDisconnectException

    def create_project(self, name: str, description: str = '', keywords: str = '', parameters: str = '') -> 'Project':
        try:
            p = self.get_project(name)
            return p
        except UnsuccessfulGetException as err:
            try:
                with self._xnat_connection as xnat:
                    xnat_project = xnat.create_project(
                        name, description, keywords)
                with PACS_DB() as db:
                    timestamp_now = datetime.now(
                        timezone).strftime("%Y-%m-%d %H:%M:%S")
                    db.insert_into_project(ProjectData(name=name, keywords=keywords, description=description,
                                           parameters=parameters, timestamp_creation=timestamp_now, timestamp_last_updated=timestamp_now))
                logger.info(f"User {self.user} created a project: {name}")
                return Project(self, name, _project_filestorage_object=xnat_project)
            except Exception as err:
                # Log the exception and raise an UnsuccessfulCreationException if project creation fails.
                msg = f"Failed to create the project: {str(err)} {str(name)}"
                logger.exception(msg)
                raise UnsuccessfulCreationException(f"{str(name)}")

    def get_project(self, name: str) -> Optional['Project']:
        try:
            project = Project(self, name)
            logger.info(f"User {self.user} retrieved information about project {project.name}.")
            return project
        except:
            msg = f"Failed to get Project '{name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Project '{name}'")

    def get_all_projects(self) -> List['Project']:
        try:
            with PACS_DB() as db:
                pjs = db.get_all_projects()
            projects = [self.get_project(project.name) for project in pjs]
            logger.info(f"User {self.user} retrieved information about project list.")
            return projects
        except Exception:
            msg = "Failed to get all Projects"
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Projects")

    def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
        try:
            d = Directory(self.get_project(project_name), directory_name)
            logger.info(f"User {self.user} retrieved information about directory {d.name}.")
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


class Project():
    def __init__(self, connection: Connection, name: str, _project_filestorage_object=None) -> None:
        self.connection = connection
        self.name = name

        try:
            with PACS_DB() as db:
                self._db_project = db.get_project_by_name(name)
        except:
            msg = f"Failed to initialize Project '{name}' from the database."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Project '{name}'")

        if _project_filestorage_object:
            self._xnat_project = _project_filestorage_object
        elif self.connection._kind == "XNAT":
            try:
                self._xnat_project = XNATProject(
                    connection._xnat_connection, name)
            except Exception as err:
                msg = f"Failed to initialize Project '{name}' from XNAT."
                logger.exception(msg)
                raise UnsuccessfulGetException(f"Projectx '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            msg = f"Unsupported connection type '{self.connection._kind}' for Project '{name}'."
            logger.exception(msg)
            raise FailedConnectionException

    @property
    def description(self) -> str:
        try:
            return self._db_project.description
        except:
            msg = f"Failed to get Project description from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project description")

    def set_description(self, description_string: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='Project', attribute_name='description', new_value=description_string, condition_column='name', condition_value=self.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.connection.user} updated the description of Project '{self.name}' to '{description_string}'")
        except:
            msg = f"Failed to set Project description for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"a new description ('{description_string}')")

    @property
    def keywords(self) -> str:
        try:
            return self._db_project.keywords
        except:
            msg = f"Failed to get Project-related keywords from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project-related keywords")

    def set_keywords(self, keywords_string: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='Project', attribute_name='keywords', new_value=keywords_string, condition_column='name', condition_value=self.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.connection.user} updated the keywords of Project '{self.name}' to '{keywords_string}'")
        except:
            msg = f"Failed to set the project keywords for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the project keywords to '{keywords_string}'")

    @property
    def parameters(self) -> str:
        try:
            return self._db_project.parameters
        except:
            msg = f"Failed to get Project-related parameters from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project-related parameters")

    def set_parameters(self, parameters_string: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='Project', attribute_name='parameters', new_value=parameters_string, condition_column='name', condition_value=self.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.connection.user} updated the parameters of Project '{self.name}' to '{parameters_string}'")
        except:
            msg = f"Failed to set the project parameters for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the project parameters to '{parameters_string}'")

    @property
    def last_updated(self) -> datetime:
        try:
            # Convert the timestamp string to a datetime object
            timestamp_datetime = datetime.strptime(
                str(self._db_project.timestamp_last_updated), "%Y-%m-%d %H:%M:%S")
            return timestamp_datetime
        except Exception as err:
            msg = f"Failed to get the timestamp of the last project update from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of the last project update" + str(err))

    def set_last_updated(self, timestamp: datetime) -> None:
        try:
            with PACS_DB() as db:
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                db.update_attribute(
                    table_name='Project', attribute_name='timestamp_last_updated', new_value=timestamp, condition_column='name', condition_value=self.name)
        except:
            msg = f"Failed to set the project's 'last_updated' to '{timestamp}' for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the project's 'last_updated' to '{timestamp}'")

    @property
    def timestamp_creation(self) -> datetime:
        try:
            # Convert the timestamp string to a datetime object
            timestamp_datetime = datetime.strptime(
                str(self._db_project.timestamp_creation), "%Y-%m-%d %H:%M:%S")
            return timestamp_datetime
        except:
            msg = f"Failed to get the timestamp of project creation from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("The timestamp of project creation")

    @property
    def owners(self) -> List[str]:
        try:
            return self._xnat_project.owners
        except:
            msg = f"Failed to get the list of Project owners from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "Project users that are assigned an 'owner' role")

    @property
    def your_user_role(self) -> str:
        try:
            return self._xnat_project.your_user_role
        except:
            msg = f"Failed to get your user role from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Your user role")

    @property
    def citations(self) -> List['CitationData']:
        try:
            with PACS_DB() as db:
                # Get List of CitationsData objects (containing id, citation string, link)
                citations = db.get_citations_for_project(self.name)
                return citations
        except:
            msg = f"Failed to get the list of Project citations from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The project citations")

    def add_citation(self, citations_string: str, link: str) -> None:
        try:
            with PACS_DB() as db:
                # Insert new citation (use cit_id 0 as this id will be generated by Postgres during insert)
                db.insert_into_citation(CitationData(
                    cit_id=0, citation=citations_string, link=link, project_name=self.name))
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.connection.user} added a citation to Project '{self.name}': '{citations_string}'")
        except:
            msg = f"Failed to add a new citation to Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException("New citation")

    def delete_citation(self, citation_id: int) -> None:
        try:
            with PACS_DB() as db:
                db.delete_citation(citation_id)
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.connection.user} deleted a citation from Project '{self.name}': '{citation_id}'")
        except:
            msg = f"Failed to delete the citation with ID {citation_id} from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException("Citation")

    def exists(self) -> bool:
        return self._xnat_project.exists()

    def download(self, destination: str) -> str:
        try:
            # Create project filder
            os.makedirs(os.path.join(destination, self.name), exist_ok=True)
            for d in self.get_all_directories():
                # Copy directories with all their subdirectories to destination
                d.download(os.path.join(destination, self.name), zip=False)
            # Zip it
            destination_zip = shutil.make_archive(os.path.join(
                destination, self.name), 'zip', destination, self.name)
            logger.info(
                f"User {self.connection.user} just downloaded the data from Project '{self.name}'.")
            return destination_zip
        except:
            msg = f"Failed to download Project '{self.name}' to the destination folder '{destination}'."
            logger.exception(msg)
            raise DownloadException

    def delete_project(self) -> None:
        try:
            with PACS_DB() as db:
                db.delete_project_by_name(self.name)
            self._xnat_project.delete_project()
            logger.info(
                f"User {self.connection.user} deleted Project '{self.name}'.")
        except:
            msg = f"Failed to delete Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"Project '{self.name}'")

    def create_directory(self, name: str, parameters: str = None) -> 'Directory':
        try:
            d = self.get_directory(name)
            return d
        except:
            try:
                with PACS_DB() as db:
                    unique_name = self.name + '::' + name
                    timestamp_now = datetime.now(
                        timezone).strftime("%Y-%m-%d %H:%M:%S")
                    db.insert_into_directory(DirectoryData(
                        unique_name=unique_name, dir_name=name, parent_project=self.name, parent_directory=None, timestamp_creation=timestamp_now, parameters=parameters, timestamp_last_updated=timestamp_now))

                dir = self._xnat_project.create_directory(unique_name)
                self.set_last_updated(datetime.now(timezone))
                logger.info(
                    f"User {self.connection.user} created a new directory named '{name}' for Project '{self.name}'.")
                return Directory(project=self, name=unique_name, _directory_filestorage_object=dir)
            except Exception as err:
                msg = f"Failed to create a new directory named '{name}' for Project '{self.name}'."
                logger.exception(msg)
                raise UnsuccessfulCreationException(str(name))

    def get_directory(self, name, _directory_filestorage_object=None) -> 'Directory':
        try:
            logger.info(
                f"User {self.connection.user} retrieved information about directory '{name}' for Project '{self.name}'.")
            return Directory(self, name=name, _directory_filestorage_object=_directory_filestorage_object)
        except:
            msg = f"Failed to get Directory '{name}' from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Directory '{name}'")

    def get_all_directories(self) -> Sequence['Directory']:
        try:
            with PACS_DB() as db:
                directories_from_db = db.get_directories_by_project(self.name)

            # Get directory objects
            filtered_directories = [self.get_directory(
                dir_data.unique_name) for dir_data in directories_from_db]

            logger.info(
                f"User {self.connection.user} retrieved information about all directories for Project '{self.name}'.")
            return filtered_directories

        except:
            msg = f"Failed to get a list of directories for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Directories")

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '', modality: str = '') -> Union['Directory', 'File']:
        try:
            if directory_name == '':
                # No desired name was given, set the name as the current timestamp
                directory_name = datetime.now(
                    timezone).strftime("%Y_%m_%d_%H_%M_%S")

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

            timestamp = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")

            # File path leads to a single file
            if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
                with PACS_DB() as db:
                    # Get the file's suffix
                    format = file_format[Path(file_path).suffix]
                    file_id = file_path.split("/")[-1]
                    updated_file_data = db.insert_into_file(
                        FileData(file_name=file_id, parent_directory=directory.name, timestamp_creation=timestamp, timestamp_last_updated=timestamp, format=format, modality=modality, tags=tags_string))

                file = self._xnat_project.insert_file_into_project(
                    file_path=file_path, file_id=updated_file_data.file_name, directory_name=directory.name, tags_string=tags_string)

                self.set_last_updated(datetime.now(timezone))
                logger.info(
                    f"User {self.connection.user} inserted a file '{file.name}' into Directory '{directory.name}' in Project '{self.name}'.")
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

                        if len(files) > 0:
                            # Handle files of current directory
                            for file_name in files:
                                # Create a FileData object
                                file_data = FileData(
                                    file_name=file_name,
                                    parent_directory=current_dir.name,
                                    format=file_format[Path(file_name).suffix],
                                    tags=tags_string,
                                    modality=modality,
                                    timestamp_creation=timestamp,
                                    timestamp_last_updated=timestamp
                                )

                                # Insert file to current directory
                                with PACS_DB() as db:
                                    updated_file_data = db.insert_into_file(
                                        file_data)
                                self._xnat_project.insert_file_into_project(
                                    file_path=os.path.join(root, file_name), file_id=updated_file_data.file_name, directory_name=current_dir.name, tags_string=tags_string)

                        directory = current_dir
                    self.set_last_updated(datetime.now(timezone))
                    logger.info(
                        f"User {self.connection.user} inserted a zip file into Directory '{directory.name}' in Project '{self.name}'.")
                return root_dir

            else:
                raise ValueError
        except ValueError:
            msg = f"File format not supported for file path: '{file_path}'."
            logger.exception(msg)
            raise WrongUploadFormatException(str(file_path.split("/")[-1]))
        except Exception as err:
            msg = f"Failed to insert a file into Project '{self.name}' from file path: '{file_path}'."
            logger.exception(msg)
            raise UnsuccessfulUploadException(str(file_path.split("/")[-1]))


class Directory():
    def __init__(self, project: Project, name: str, _directory_filestorage_object=None) -> None:
        self.name = name  # unique
        self.display_name = self.name.split('::')[-1]
        self.project = project

        try:
            with PACS_DB() as db:
                self._db_directory = db.get_directory_by_name(name)

        except:
            msg = f"Failed to initialize Directory '{name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Directory '{name}'")

        if _directory_filestorage_object:
            self._xnat_directory = _directory_filestorage_object
        elif self.project.connection._kind == "XNAT":
            try:
                self._xnat_directory = XNATDirectory(
                    project._xnat_project, name)
            except:
                msg = f"Failed to initialize XNATDirectory for '{name}'"
                logger.exception(msg)
                raise UnsuccessfulGetException(f"Directory '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            msg = f"Failed to initialize Directory '{name}' due to unsupported connection type"
            logger.exception(msg)
            raise FailedConnectionException

    @property
    def number_of_files(self) -> int:
        try:
            total_files = len(self.get_all_files())

            # Recursively calculate the number of files in subdirectories
            for subdirectory in self.get_subdirectories():
                total_files += subdirectory.number_of_files

            return total_files
        except Exception as e:
            msg = f"Failed to get the number of files for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def parent_directory(self) -> 'Directory':
        try:
            return self.project.get_directory(self._db_directory.parent_directory)
        except:
            msg = f"Failed to get the parent directory for '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Parent directory name")

    @property
    def parameters(self) -> str:
        try:
            return self._db_directory.parameters
        except:
            msg = f"Failed to get the parameters for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Directory-related parameters")

    def set_parameters(self, parameters_string: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='Directory', attribute_name='parameters', new_value=parameters_string, condition_column='unique_name', condition_value=self.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.project.connection.user} set parameters for Directory '{self.name}' to '{parameters_string}'.")
        except:
            msg = f"Failed to set parameters for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the directory parameters to '{parameters_string}'")

    @property
    def last_updated(self) -> str:
        try:
            return self._db_directory.timestamp_last_updated
        except:
            msg = f"Failed to get the last updated timestamp for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of the last directory update")

    def set_last_updated(self, timestamp: datetime) -> None:
        try:
            with PACS_DB() as db:
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                db.update_attribute(
                    table_name='Directory', attribute_name='timestamp_last_updated', new_value=timestamp, condition_column='unique_name', condition_value=self.name)
        except:
            msg = f"Failed to set the last updated timestamp for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the directory's 'last_updated' to '{timestamp}'")

    @property
    def timestamp_creation(self) -> str:
        try:
            return self._db_directory.timestamp_creation
        except:
            msg = f"Failed to get the creation timestamp for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of directory creation")

    def exists(self) -> bool:
        return self._xnat_directory.exists()

    def delete_directory(self) -> None:
        try:
            for subdir in self.get_subdirectories():
                subdir.delete_directory()
            with PACS_DB() as db:
                db.delete_directory_by_name(self.name)

            # Update the parents last updated
            if self._db_directory.parent_directory == None:
                # Top level directory -> change last updated of project
                self.project.set_last_updated(datetime.now(timezone))
            else:
                self.parent_directory.set_last_updated(datetime.now(timezone))
            logger.info(
                f"User {self.project.connection.user} deleted directory '{self.name}'.")

        except:
            msg = f"Failed to delete directory '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"directory '{self.name}'")

    def create_subdirectory(self, name: str, parameters: str = '') -> 'Directory':
        try:
            d = self.project.get_directory(self.name + '::' + name)
            return d
        except:
            try:
                with PACS_DB() as db:
                    unique_name = self.name + '::' + name
                    timestamp_now = datetime.now(
                        timezone).strftime("%Y-%m-%d %H:%M:%S")
                    db.insert_into_directory(DirectoryData(
                        unique_name=unique_name, dir_name=name, parent_project=None, parent_directory=self.name, timestamp_creation=timestamp_now, parameters=parameters, timestamp_last_updated=timestamp_now, ))

                dir = self.project._xnat_project.create_directory(unique_name)
                self.set_last_updated(datetime.now(timezone))

                logger.info(
                    f"User {self.project.connection.user} created subdirectory '{name}' in directory '{self.name}'.")
                return Directory(project=self.project, name=unique_name, _directory_filestorage_object=dir)

            except Exception:
                msg = f"Failed to create subdirectory '{name}' in directory '{self.name}'."
                logger.exception(msg)
                raise UnsuccessfulCreationException(str(name))

    def get_subdirectories(self) -> List['Directory']:
        try:
            with PACS_DB() as db:
                subdirectories_from_db = db.get_subdirectories_by_directory(
                    self.name)

            # Only return the directories that are subdirectories of this directory
            filtered_directories = [
                Directory(self.project, d.unique_name) for d in subdirectories_from_db]
            
            logger.info(f"User {self.project.connection.user} retrieved information about subdirectories for directory '{self.name}'.")
            return filtered_directories
        except:
            msg = f"Failed to get subdirectories for directory '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    def get_file(self, file_name: str, _file_filestorage_object=None) -> 'File':
        try:
            file = File(self, name=file_name, _file_filestorage_object=_file_filestorage_object)
            return file
        except:
            msg = f"Failed to get file '{file_name}' in directory '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"File '{file_name}'")

    def get_all_files(self) -> List['File']:
        try:
            fs = self._xnat_directory.get_all_files()
            files = [self.get_file(
                file_name=f.name, _file_filestorage_object=f) for f in fs]
            logger.info(f"User {self.project.connection.user} retrieved information about all files for directory '{self.name}'.")
            return files
        except:
            msg = f"Failed to get all files for directory '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Files")

    def download(self, destination, zip: bool = True) -> str:
        self._create_folders_and_copy_files_for_download(destination)
        if zip:
            destination_zip = shutil.make_archive(os.path.join(
                destination, self.display_name), 'zip', destination, self.display_name)
            logger.info(f"User {self.project.connection.user} downloaded all files for directory '{self.name}'.")
            return destination_zip
        else:
            msg = f"Failed to download directory '{self.name}'."
            logger.exception(msg)
            return destination

    def _create_folders_and_copy_files_for_download(self, target_folder):
        current_folder = os.path.join(target_folder, self.display_name)
        os.makedirs(current_folder, exist_ok=True)

        try:
            for file in self.get_all_files():
                # Copy files to the current folder
                file._xnat_file.download(current_folder)
        except Exception as e:
            msg = f"Failed to copy files for download in directory '{self.name}'."
            logger.exception(msg)
            raise DownloadException

        for subdirectory in self.get_subdirectories():
            try:
                subdirectory._create_folders_and_copy_files_for_download(
                    current_folder)
            except Exception as e:
                msg = f"Failed to copy files for download in subdirectory '{subdirectory.name}' of directory '{self.name}'."
                logger.exception(msg)
                raise DownloadException


class File():
    def __init__(self, directory: Directory, name: str, _file_filestorage_object=None) -> None:
        self.directory = directory
        self.name = name

        try:
            with PACS_DB() as db:
                self._db_file = db.get_file_by_name_and_directory(
                    self.name, self.directory.name)
        except:
            msg = f"Failed to get DB-File '{name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"DB-File '{name}'")

        if _file_filestorage_object:
            self._xnat_file = _file_filestorage_object
        elif self.directory.project.connection._kind == "XNAT":
            try:
                self._xnat_file = XNATFile(directory._xnat_directory, name)
                msg = f"Failed to get File '{name}' in directory '{self.directory.name}'."
                logger.exception(msg)
            except:
                raise UnsuccessfulGetException(f"File '{name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def format(self) -> str:
        try:
            return self._db_file.format
        except:
            msg = f"Failed to get format for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File format")

    @property
    def tags(self) -> str:
        try:
            return self._db_file.tags
        except:
            msg = f"Failed to get tags for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File tags")

    def set_tags(self, tags: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='File', attribute_name='tags', new_value=tags, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(f"User {self.directory.project.connection.user} set tags for File '{self.name}' in directory '{self.directory.name}' to '{tags}'.")
        except:
            msg = f"Failed to update tags for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'modality' to '{tags}'")

    @property
    def modality(self) -> str:
        try:
            return self._db_file.modality
        except:
            msg = f"Failed to get modality for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File modality")

    def set_modality(self, modality: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='File', attribute_name='modality', new_value=modality, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.name)
            self.set_last_updated(datetime.now(timezone))
            logger.info(f"User {self.directory.project.connection.user} set modality for File '{self.name}' in directory '{self.directory.name}' to '{modality}'.")
        except:
            msg = f"Failed to update modality for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'modality' to '{modality}'")

    @property
    def timestamp_creation(self) -> str:
        try:
            return self._db_file.timestamp_creation
        except:
            msg = f"Failed to get creation timestamp for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File creation timestamp")

    @property
    def last_updated(self) -> str:
        try:
            return self._db_file.timestamp_last_updated
        except:
            msg = f"Failed to get last update timestamp for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File last update timestamp")

    def set_last_updated(self, timestamp: datetime) -> None:
        try:
            with PACS_DB() as db:
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                db.update_attribute(
                    table_name='File', attribute_name='timestamp_last_updated', new_value=timestamp, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.name)
        except:
            msg = f"Failed to update last_updated timestamp for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'last_updated' to '{timestamp}'")

    @property
    def content_type(self) -> str:
        try:
            return self._xnat_file.content_type
        except:
            msg = f"Failed to get content type for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File content type")

    @property
    def size(self) -> int:
        try:
            return self._xnat_file.size
        except:
            msg = f"Failed to get size for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File size")

    @property
    def data(self) -> bytes:
        try:
            return self._xnat_file.data
        except:
            msg = f"Failed to get file data for File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("The actual file data itself")

    def exists(self) -> bool:
        return self._xnat_file.exists()

    def download(self, destination: str = '') -> str:
        try:
            logger.info(f"User {self.directory.project.connection.user} downloaded File '{self.name}' from {self.directory.name}.")
            return self._xnat_file.download(destination)
        except:
            msg = f"Failed to download File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise DownloadException

    def delete_file(self) -> None:
        try:
            self._xnat_file.delete_file()

            with PACS_DB() as db:
                db.delete_file_by_name(self.name)

            self.directory.set_last_updated(datetime.now(timezone))
            logger.info(f"User {self.directory.project.connection.user} deleted File '{self.name}' from {self.directory.name}.")

        except:
            msg = f"Failed to delete File '{self.name}' in directory '{self.directory.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"file '{self.name}'")
