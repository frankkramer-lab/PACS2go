import json
import os
import shutil
from datetime import datetime
from typing import List

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB, DirectoryData
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulCreationException,
    UnsuccessfulDeletionException, UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.pacs_data_interface.file import File
#from pacs2go.data_interface.pacs_data_interface.project import Project # only for typing, but creates circular import
from pacs2go.data_interface.xnat_rest_wrapper import XNATDirectory


class Directory:
    this_timezone = timezone("Europe/Berlin")

    def __init__(self, project, name: str, parent_dir:'Directory' = None, parameters:str = "") -> None:
        self.display_name = name.rsplit('::',1)[-1] # Get Directory name
        self.project = project
        self._file_store_directory = None
        self.is_consistent = True

        try:
            with PACS_DB() as db:
                self._db_directory = db.get_directory_by_name(name)
                if self._db_directory is None:
                    # Create directory in DB and in file store
                    if not parent_dir:
                        self._file_store_directory, self._db_directory = self.project.create_directory(unique_name=self.project.name + "::" + self.display_name, parameters=parameters)
                    else:
                        self._file_store_directory, self._db_directory = parent_dir.create_subdirectory(unique_name=parent_dir.unique_name + "::" + self.display_name, parameters=parameters)
                self.unique_name = self._db_directory.unique_name

        except:
            msg = f"Failed to create Directory '{name}' at initialization."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Directory '{name}'")

        if not self._file_store_directory:
            # Get file store object
            if self.project.connection._kind == "XNAT":
                try:
                    self._file_store_directory = XNATDirectory(
                        project._file_store_project, name)
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
            with PACS_DB() as db:
                total_files = db.get_numberoffiles_under_directory(self.unique_name)

            return total_files
        except Exception:
            msg = f"Failed to get the number of files for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)
        
    @property
    def number_of_files_on_this_level(self) -> int:
        try:
            with PACS_DB() as db:
                return db.get_numberoffiles_within_directory(self.unique_name)

        except Exception:
            msg = f"Failed to get the number of files on this level for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def parent_directory(self) -> 'Directory':
        try:
            if self._db_directory.parent_directory:
                return self.project.get_directory(self._db_directory.parent_directory)
        except:
            msg = f"Failed to get the parent directory for '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Parent directory name")

    @property
    def parameters(self) -> str:
        try:
            return self._db_directory.parameters
        except:
            msg = f"Failed to get the parameters for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Directory-related parameters")

    def set_parameters(self, parameters_string: str) -> None:
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='Directory', attribute_name='parameters', new_value=parameters_string, condition_column='unique_name', condition_value=self.unique_name)
            self.set_last_updated(datetime.now(self.this_timezone))
            logger.info(
                f"User {self.project.connection.user} set parameters for Directory '{self.unique_name}' to '{parameters_string}'.")
        except:
            msg = f"Failed to set parameters for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the directory parameters to '{parameters_string}'")

    @property
    def last_updated(self) -> str:
        try:
            return self._db_directory.timestamp_last_updated
        except:
            msg = f"Failed to get the last updated timestamp for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of the last directory update")

    def set_last_updated(self, timestamp: datetime) -> None:
        try:
            with PACS_DB() as db:
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                db.update_attribute(
                    table_name='Directory', attribute_name='timestamp_last_updated', new_value=timestamp, condition_column='unique_name', condition_value=self.unique_name)
        except:
            msg = f"Failed to set the last updated timestamp for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the directory's 'last_updated' to '{timestamp}'")

    @property
    def timestamp_creation(self) -> str:
        try:
            return self._db_directory.timestamp_creation
        except:
            msg = f"Failed to get the creation timestamp for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of directory creation")

    def is_favorite(self, username) -> bool:
        try:
            with PACS_DB() as db:
                return db.is_favorited_by_user(self.unique_name, username) 
        except:
            msg = f"Failed to get 'favorite' status for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "the 'favorite' status of this directory")            

    def exists(self) -> bool:
        return self._file_store_directory.exists()

    def delete_directory(self) -> None:
        try:
            for subdir in self.get_subdirectories():
                subdir.delete_directory()
            with PACS_DB() as db:
                db.delete_directory_by_name(self.unique_name)

            # Update the parents last updated
            self.project.set_last_updated(datetime.now(self.this_timezone))
            if self.parent_directory:
                self.parent_directory.set_last_updated(datetime.now(self.this_timezone))
            logger.info(
                f"User {self.project.connection.user} deleted directory '{self.unique_name}'.")

        except:
            msg = f"Failed to delete directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"directory '{self.unique_name}'")

    def create_subdirectory(self, unique_name: str, parameters: str = ''):
        try:
            with PACS_DB() as db:
                timestamp_now = datetime.now(
                    self.this_timezone).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"insert {unique_name}")
                # Insert into DB
                db.insert_into_directory(DirectoryData(
                    unique_name=unique_name, dir_name=unique_name.rsplit("::",1)[-1], parent_project=None, parent_directory=self.unique_name, timestamp_creation=timestamp_now, parameters=parameters, timestamp_last_updated=timestamp_now, ))
                db_dir = db.get_directory_by_name(unique_name)

            # Upload to file store
            file_store_dir = self.project._file_store_project.create_directory(unique_name)

            self.set_last_updated(datetime.now(self.this_timezone))

            logger.info(
                f"User {self.project.connection.user} created subdirectory '{unique_name}' in directory '{self.unique_name}'.")
            return file_store_dir, db_dir
        except Exception:
            msg = f"Failed to create subdirectory '{unique_name}' in directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulCreationException(str(unique_name))

    def get_subdirectories(self) -> List['Directory']:
        try:
            with PACS_DB() as db:
                subdirectories_from_db = db.get_subdirectories_by_directory(
                    self.unique_name)

            # Only return the directories that are subdirectories of this directory
            filtered_directories = [
                Directory(self.project, d.unique_name) for d in subdirectories_from_db]

            # Check for inconsistencies and log as warning
            if len(subdirectories_from_db) != len(filtered_directories):
                logger.warning(f"There might be inconsistencies concerning Project {self.unique_name}.")
            
            logger.debug(f"User {self.project.connection.user} retrieved information about subdirectories for directory '{self.unique_name}'.")
            return filtered_directories
        except:
            msg = f"Failed to get subdirectories for directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    def get_file(self, file_name: str, _file_filestorage_object=None) -> 'File':
        try:
            file = File(self, name=file_name, _file_filestorage_object=_file_filestorage_object)
            return file
        except:
            msg = f"Failed to get file '{file_name}' in directory '{self.unique_name}'."
            logger.exception(msg)
            return None

    def get_all_files(self) -> List['File']:
        try:
            # Get all files, necessary for file viewer
            # Retrieval via file store logic to make sure that the physical file really exists and is not merely a db entry
            fs = self._file_store_directory.get_all_files()
            files = [self.get_file(
                file_name=f.name, _file_filestorage_object=f) for f in fs]

            
            if any(file is None for file in files):
                # Handle the case where at least one file is None (failed to retrieve from DB)
                logger.warning(f"At least one file in directory '{self.unique_name}' could not be retrieved.")
                self.is_consistent = False
                # Clean up None entries in files list
                files = [file for file in files if file is not None]
            
            logger.debug(f"User {self.project.connection.user} retrieved information about all files for directory '{self.unique_name}'.")

            files = [i for i in files if i is not None]
            return files
        except:
            msg = f"Failed to get all files for directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Files")

    def get_all_files_sliced_and_as_json(self,  filter:str= '', quantity:int = 20, offset:int = 0) -> dict:
        try:
            # Only get files from a specific range (quantity and offset)
            with PACS_DB() as db:
                files_data = db.get_directory_files_slice(directory_name=self.unique_name, filter=filter, quantity=quantity, offset=offset)

            files = [ { 
            'name': f.file_name,
            'format': f.format,
            'modality': f.modality,
            'tags': f.tags,
            'size': float(f.size) if f.size else 0,
            'upload': f.timestamp_creation.strftime("%d.%B %Y, %H:%M:%S"),
            'associated_directory': f.parent_directory,
            'associated_project': self.project.name,
            'user_rights': self.project.your_user_role
                    } for f in files_data]
            return json.dumps(files)
        except:
            msg = f"Failed to get all files for directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Files")

    def favorite_directory(self, username:str) -> None:
        try:
            with PACS_DB() as db:
                db.insert_favorite_directory(self.unique_name, username)
        except:
            msg = f"Failed to set favorite for Directory '{self.unique_name}' and {username}"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the users's favorite directories.")
    
    def remove_favorite_directory(self, username:str) -> None:
        try:
            with PACS_DB() as db:
                db.delete_favorite(self.unique_name, username)
        except:
            msg = f"Failed to un-favorite for Directory '{self.unique_name}' and {username}"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the users's favorite directories.")

    def download(self, destination, zip: bool = True) -> str:
        self._create_folders_and_copy_files_for_download(destination)
        if zip:
            destination_zip = shutil.make_archive(os.path.join(
                destination, self.display_name), 'zip', destination, self.display_name)
            logger.info(f"User {self.project.connection.user} downloaded all files for directory '{self.unique_name}'.")
            return destination_zip
        else:
            msg = f"Failed to download directory '{self.unique_name}'."
            logger.exception(msg)
            return destination

    def _create_folders_and_copy_files_for_download(self, target_folder):
        current_folder = os.path.join(target_folder, self.display_name)
        os.makedirs(current_folder, exist_ok=True)

        try:
            for file in self.get_all_files():
                # Copy files to the current folder
                file._file_store_file.download(current_folder)
        except Exception:
            msg = f"Failed to copy files for download in directory '{self.unique_name}'."
            logger.exception(msg)
            raise DownloadException

        for subdirectory in self.get_subdirectories():
            try:
                subdirectory._create_folders_and_copy_files_for_download(
                    current_folder)
            except Exception:
                msg = f"Failed to copy files for download in subdirectory '{subdirectory.unique_name}' of directory '{self.unique_name}'."
                logger.exception(msg)
                raise DownloadException
            
    def to_dict(self) -> dict:
        """
        Convert various attributes of the Directory object to a dictionary for serialization.
        """
        return {
            'unique_name': self.unique_name,
            'display_name': self.display_name,
            'timestamp_creation': self.timestamp_creation.strftime("%d.%B %Y, %H:%M:%S"),
            'last_updated': self.last_updated.strftime("%d.%B %Y, %H:%M:%S"),     
            'is_consistent': self.is_consistent,   
            'parameters': self.parameters,
            'number_of_files': self.number_of_files,  
            'associated_directory': self.parent_directory.unique_name if self.parent_directory else None,
            'associated_project': self.project.name,
            'user_rights': self.project.your_user_role,  
        }