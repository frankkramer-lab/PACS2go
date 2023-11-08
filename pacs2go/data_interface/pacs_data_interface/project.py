import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Union

from pytz import timezone

from pacs2go.data_interface.data_structure_db import (PACS_DB, CitationData,
                                                      DirectoryData, FileData)
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulCreationException,
    UnsuccessfulDeletionException, UnsuccessfulGetException,
    UnsuccessfulUploadException, WrongUploadFormatException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.pacs_data_interface.connection import Connection
from pacs2go.data_interface.pacs_data_interface.directory import Directory
from pacs2go.data_interface.pacs_data_interface.file import File
from pacs2go.data_interface.xnat_rest_wrapper import XNATProject


class Project:
    # File format metadata
    file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI',
                '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT'}

    this_timezone = timezone("Europe/Berlin")

    def __init__(self, connection: Connection, name: str, _project_file_store_object=None) -> None:
        self.connection = connection
        self.name = name

        try:
            # Retrieve Project from database table
            with PACS_DB() as db:
                self._db_project = db.get_project_by_name(name)
        except:
            msg = f"Failed to initialize Project '{name}' from the database."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Project '{name}'")

        # On creation the file store object is passed directly to the constructor
        if _project_file_store_object:
            self._file_store_project = _project_file_store_object
        elif self.connection._kind == "XNAT":
            try:
                # Retrieve file storage object
                self._file_store_project = XNATProject(
                    connection._file_store_connection, name)
            except Exception:
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
            self.set_last_updated(datetime.now(self.this_timezone))
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
            self.set_last_updated(datetime.now(self.this_timezone))
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
            self.set_last_updated(datetime.now(self.this_timezone))
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
            return self._file_store_project.owners
        except:
            msg = f"Failed to get the list of Project owners from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "Project users that are assigned an 'owner' role")

    @property
    def your_user_role(self) -> str:
        try:
            return self._file_store_project.your_user_role
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
            self.set_last_updated(datetime.now(self.this_timezone))
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
            self.set_last_updated(datetime.now(self.this_timezone))
            logger.info(
                f"User {self.connection.user} deleted a citation from Project '{self.name}': '{citation_id}'")
        except:
            msg = f"Failed to delete the citation with ID {citation_id} from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException("Citation")

    def exists(self) -> bool:
        return self._file_store_project.exists()

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
            self._file_store_project.delete_project()
            logger.info(
                f"User {self.connection.user} deleted Project '{self.name}'.")
        except:
            msg = f"Failed to delete Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"Project '{self.name}'")

    def create_directory(self, unique_name: str, parameters: str = None):
        try:
            with PACS_DB() as db:
                timestamp_now = datetime.now(
                    self.this_timezone).strftime("%Y-%m-%d %H:%M:%S")
                # Insert into DB
                db.insert_into_directory(DirectoryData(
                    unique_name=unique_name, dir_name=unique_name.split('::')[-1], parent_project=self.name, parent_directory=None, timestamp_creation=timestamp_now, parameters=parameters, timestamp_last_updated=timestamp_now))
                db_dir = db.get_directory_by_name(unique_name)
            # Upload to file store
            file_store_dir = self._file_store_project.create_directory(unique_name)
            
            self.set_last_updated(datetime.now(self.this_timezone))

            logger.info(
                f"User {self.connection.user} created a new directory named '{unique_name}' for Project '{self.name}'.")
            return file_store_dir, db_dir
        except Exception:
            msg = f"Failed to create a new directory named '{unique_name}' for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulCreationException(str(unique_name.split('::')[-1]))

    def get_directory(self, name, _directory_filestorage_object=None) -> 'Directory':
        try:
            logger.debug(
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

            # Check for inconsistencies and log as warning
            if len(directories_from_db) != len(filtered_directories):
                logger.warning(f"There might be inconsistencies concerning Project {self.name}.")

            logger.debug(
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
                    self.this_timezone).strftime("%Y_%m_%d_%H_%M_%S")

            if directory_name.count('::') == 1 or directory_name.count('::') == 0:
                # Name is not an inherited name and is directly under a project, create/get directory
                directory = Directory(self, directory_name)

            else:
                # Get the parent directory of what is a subdirectory (contains a -) by its unique name
                parent_dir = self.get_directory(
                    directory_name.rsplit('::', 1)[0])

                # Create/get the subdirectory from parent directory TODO
                directory = Directory(self, directory_name, parent_dir=parent_dir)
                # directory = parent_dir.create_subdirectory(
                #     directory_name.rsplit('::', 1)[-1])

            timestamp = datetime.now(self.this_timezone).strftime("%Y-%m-%d %H:%M:%S")

            # File path leads to a single file
            if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
                with PACS_DB() as db:
                    # Get the file's suffix
                    format = self.file_format[Path(file_path).suffix]
                    file_id = file_path.split("/")[-1]
                    # Insert file into DB
                    updated_file_data = db.insert_into_file(
                        FileData(file_name=file_id, parent_directory=directory.name, timestamp_creation=timestamp, timestamp_last_updated=timestamp, format=format, modality=modality, tags=tags_string))

                # Upload file to file store
                file_store_file_object = self._file_store_project.insert_file_into_project(
                    file_path=file_path, file_id=updated_file_data.file_name, directory_name=directory.name, tags_string=tags_string)

                self.set_last_updated(datetime.now(self.this_timezone))
                logger.info(
                    f"User {self.connection.user} inserted a file '{file_store_file_object.name}' into Directory '{directory.name}' in Project '{self.name}'.")
                return File(directory=directory, name=file_store_file_object.name, _file_filestorage_object=file_store_file_object)

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
                            current_dir = Directory(self, os.path.basename(root), parent_dir=directory)

                        if len(files) > 0:
                            # Handle files of current directory
                            for file_name in files:
                                # Create a FileData object
                                file_data = FileData(
                                    file_name=file_name,
                                    parent_directory=current_dir.name,
                                    format=self.file_format[Path(file_name).suffix],
                                    tags=tags_string,
                                    modality=modality,
                                    timestamp_creation=timestamp,
                                    timestamp_last_updated=timestamp
                                )

                                # Insert file to current directory
                                with PACS_DB() as db:
                                    # Insert into DB
                                    updated_file_data = db.insert_into_file(
                                        file_data)
                                    logger.info(f"insert {updated_file_data.file_name}, {updated_file_data.parent_directory}")

                                # Upload to file store
                                self._file_store_project.insert_file_into_project(
                                    file_path=os.path.join(root, file_name), file_id=updated_file_data.file_name, directory_name=current_dir.name, tags_string=tags_string)

                        directory = current_dir

                    self.set_last_updated(datetime.now(self.this_timezone))
                    logger.info(
                        f"User {self.connection.user} inserted a zip file into Directory '{directory.name}' in Project '{self.name}'.")
                return root_dir

            else:
                raise ValueError
            
        except ValueError:
            msg = f"File format not supported for file path: '{file_path}'."
            logger.exception(msg)
            raise WrongUploadFormatException(str(file_path.split("/")[-1]))
        
        except Exception:
            msg = f"Failed to insert a file into Project '{self.name}' from file path: '{file_path}'."
            logger.exception(msg)
            raise UnsuccessfulUploadException(str(file_path.split("/")[-1]))

