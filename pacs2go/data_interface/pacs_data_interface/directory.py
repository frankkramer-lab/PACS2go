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
from pacs2go.data_interface.xnat_rest_wrapper import XNATDirectory


class Directory:
    """Represents a directory within the PACS system, providing methods to manage subdirectories and files."""

    this_timezone = timezone("Europe/Berlin")

    def __init__(self, project, name: str, parent_dir:'Directory' = None, parameters:str = "") -> None:
        """
        Initializes a Directory object.

        Args:
            project (Project): The project to which this directory belongs. (Not typed due to circular import.)
            name (str): The name of the directory.
            parent_dir (Directory, optional): The parent directory. Defaults to None.
            parameters (str, optional): Additional parameters for the directory. Defaults to "".

        Raises:
            UnsuccessfulCreationException: If the directory cannot be created.
            UnsuccessfulGetException: If the directory cannot be retrieved.
            FailedConnectionException: If the connection type is unsupported.
        """
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
            raise UnsuccessfulCreationException(f"'{name}'")

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
    def number_of_subdirectories(self) -> int:
        """
        Returns the number of subdirectories within this directory (Direct children). 

        Returns:
            int: The number of subdirectories.

        Raises:
            UnsuccessfulGetException: If the number of subdirectories cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                total = db.get_numberofsubdirectories_under_directory(self.unique_name)
            return total
        except Exception:
            msg = f"Failed to get the number of directories for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def number_of_files(self) -> int:
        """
        Returns the total number of files within this directory. Use number_of_files_on_this_level() to only retrieve file count in this directory.

        Returns:
            int: The total number of files.

        Raises:
            UnsuccessfulGetException: If the number of files cannot be retrieved.
        """
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
        """
        Returns the number of files within this directory on the current level.

        Returns:
            int: The number of files on this level.

        Raises:
            UnsuccessfulGetException: If the number of files cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                return db.get_numberoffiles_within_directory(self.unique_name)

        except Exception:
            msg = f"Failed to get the number of files on this level for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def parent_directory(self) -> 'Directory':
        """
        Returns the parent directory of this directory if directory is a subdirectory. Othewise an empty string is returned

        Returns:
            Directory: The parent directory.

        Raises:
            UnsuccessfulGetException: If the parent directory cannot be retrieved.
        """
        try:
            if self._db_directory.parent_directory:
                return self.project.get_directory(self._db_directory.parent_directory)
            else:
                return ''
        except:
            msg = f"Failed to get the parent directory for '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Parent directory name")

    @property
    def parameters(self) -> str:
        """
        Returns the parameters associated with this directory.

        Returns:
            str: The user-defined parameters.

        Raises:
            UnsuccessfulGetException: If the parameters cannot be retrieved.
        """
        try:
            return self._db_directory.parameters
        except:
            msg = f"Failed to get the parameters for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException("Directory-related parameters")

    def set_parameters(self, parameters_string: str) -> None:
        """
        Sets the parameters for this directory.

        Args:
            parameters_string (str): The new parameters for the directory.

        Raises:
            UnsuccessfulAttributeUpdateException: If the parameters cannot be updated.
        """
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
        """
        Returns the timestamp of the last update for this directory.

        Returns:
            str: The last updated timestamp.

        Raises:
            UnsuccessfulGetException: If the timestamp cannot be retrieved.
        """
        try:
            return self._db_directory.timestamp_last_updated
        except:
            msg = f"Failed to get the last updated timestamp for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of the last directory update")

    def set_last_updated(self, timestamp: datetime) -> None:
        """
        Sets the last updated timestamp for this directory.

        Args:
            timestamp (datetime): The new timestamp.

        Raises:
            UnsuccessfulAttributeUpdateException: If the timestamp cannot be updated.
        """
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
        """
        Returns the timestamp of when this directory was initially created.

        Returns:
            str: The creation timestamp.

        Raises:
            UnsuccessfulGetException: If the timestamp cannot be retrieved.
        """
        try:
            return self._db_directory.timestamp_creation
        except:
            msg = f"Failed to get the creation timestamp for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "The timestamp of directory creation")

    def is_favorite(self, username) -> bool:
        """
        Checks if this directory is marked as favorite by the specified user.

        Args:
            username (str): The username to check.

        Returns:
            bool: True if the directory is a favorite, False otherwise.

        Raises:
            UnsuccessfulGetException: If the favorite status cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                return db.is_favorited_by_user(self.unique_name, username) 
        except:
            msg = f"Failed to get 'favorite' status for Directory '{self.unique_name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "the 'favorite' status of this directory")            

    def exists(self) -> bool:
        """
        Checks if the directory exists in the file store.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        return self._file_store_directory.exists()
    
    def update_user_activity(self, username: str) -> None:
        """
        Updates the last activity timestamp for a user in relation to this directory. Necessary to visualize "while you were gone" updates to user.

        Args:
            username (str): The username to update.

        Raises:
            UnsuccessfulGetException: If the user activity cannot be updated.
        """
        try:
            with PACS_DB() as db:
                db.update_user_activity(username, self.unique_name)
        except:
            msg = f"Failed to update user activity for Directory '{self.unique_name}' and user '{username}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "the 'user's last activity' status for this directory")    

    def delete_directory(self) -> None:
        """
        Deletes this directory and all its subdirectories.

        Raises:
            UnsuccessfulDeletionException: If the directory cannot be deleted.
        """
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

    def create_subdirectory(self, unique_name: str, parameters: str = '') -> tuple:
        """
        Creates a subdirectory within this directory.

        Args:
            unique_name (str): The unique name for the subdirectory.
            parameters (str, optional): Additional parameters for the subdirectory. Defaults to ''.

        Returns:
            Tuple: A tuple containing the file store directory and the database directory object.

        Raises:
            UnsuccessfulCreationException: If the subdirectory cannot be created.
        """
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

    def get_subdirectories(self, filter:str= None, offset:int = None, quantity:int = None) -> List['Directory']:
        """
        Retrieves a list of subdirectories within this directory. Offset and Quantity allow for pagination optimization.

        Args:
            filter (str, optional): Filter for subdirectory retrieval. Defaults to None.
            offset (int, optional): Offset for subdirectory retrieval. Defaults to None.
            quantity (int, optional): Quantity of subdirectories to retrieve. Defaults to None.

        Returns:
            List[Directory]: A list of subdirectories.

        Raises:
            UnsuccessfulGetException: If subdirectories cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                subdirectories_from_db = db.get_subdirectories_by_directory(
                    self.unique_name, filter, offset, quantity)

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
        """
        Retrieves a file from this directory.

        Args:
            file_name (str): The name of the file.
            _file_filestorage_object (optional): The file storage object. Defaults to None.

        Returns:
            File: The file object.

        Raises:
            UnsuccessfulGetException: If the file cannot be retrieved.
        """
        try:
            file = File(self, name=file_name, _file_filestorage_object=_file_filestorage_object)
            return file
        except:
            msg = f"Failed to get file '{file_name}' in directory '{self.unique_name}'."
            logger.exception(msg)
            return None

    def get_all_files(self) -> List['File']:
        """
        Retrieves all files within this directory.

        Returns:
            List[File]: A list of file objects.

        Raises:
            UnsuccessfulGetException: If the files cannot be retrieved.
        """
        try:
            # Get all files, necessary for file viewer
            # Retrieval via file store logic to make sure that the physical file really exists and is not merely a db entry.
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

    def get_all_files_sliced_and_as_json(self,  filter:str= '', quantity:int = None, offset:int = 0) -> dict:
        """
        Retrieves a sliced list of files as a JSON object. Offset and Quantity allow for pagination optimization.

        Args:
            filter (str, optional): Filter for file retrieval. Defaults to ''.
            quantity (int, optional): Quantity of files to retrieve. Defaults to None.
            offset (int, optional): Offset for file retrieval. Defaults to 0.

        Returns:
            dict: A JSON object containing file information.

        Raises:
            UnsuccessfulGetException: If the files cannot be retrieved.
        """
        if quantity is None:
            quantity = self.number_of_files_on_this_level
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
            'last_updated': f.timestamp_last_updated.strftime("%d.%B %Y, %H:%M:%S"),
            'associated_directory': f.parent_directory,
            'associated_project': self.project.name,
            'user_rights': self.project.your_user_role
                    } for f in files_data]
            return json.dumps(files)
        except:
            msg = f"Failed to get all files for directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Files")

    def get_new_files_for_user(self, username:str) -> list:
        """
        Retrieves new files for a specific user within this directory.

        Args:
            username (str): The username to retrieve new files for.

        Returns:
            list: A list of new file names.

        Raises:
            UnsuccessfulGetException: If the new files cannot be retrieved.
        """
        try:
            # Only get files from a specific range (quantity and offset)
            with PACS_DB() as db:
                file_names = db.get_new_files_for_user(username, self.unique_name)
            return file_names
        except:
            msg = f"Failed to get new files for directory '{self.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("New files")
        
    def update_multiple_files(self, file_names:list, modality:str, tags:str) -> None:
        """
        Updates multiple files within this directory.

        Args:
            file_names (list): List of file names to update.
            modality (str): The new modality for the files.
            tags (str): The new tags for the files.

        Raises:
            UnsuccessfulAttributeUpdateException: If the files cannot be updated.
        """
        try:
            with PACS_DB() as db:
                db.update_multiple_files(file_names, modality, tags, self.unique_name)
            logger.info(
                f"User {self.project.connection.user} updated multiple filese in directory '{self.unique_name}': {file_names}.")
        except:
            msg = f"Failed to update files for directory '{self.unique_name}': {file_names}"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(f"Multiple files in {self.unique_name}")
        
    def delete_multiple_files(self, file_names:list) -> None:
        """
        Deletes multiple files within this directory.

        Args:
            file_names (list): List of file names to delete.

        Raises:
            UnsuccessfulDeletionException: If the files cannot be deleted.
        """
        try:
            with PACS_DB() as db:
                db.delete_multiple_files_by_name(file_names=file_names, directory_name=self.unique_name)
            self.set_last_updated(datetime.now(self.this_timezone))
            logger.info(
                f"User {self.project.connection.user} deleted multiple filese in directory '{self.unique_name}': {file_names}.")
        except:
            msg = f"Failed to delete files for directory '{self.unique_name}': {file_names}"
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"Multiple files in {self.unique_name}")

    def favorite_directory(self, username:str) -> None:
        """
        Marks this directory as a favorite for a user.

        Args:
            username (str): The username to mark the directory as favorite for.

        Raises:
            UnsuccessfulAttributeUpdateException: If the directory cannot be marked as favorite.
        """
        try:
            with PACS_DB() as db:
                db.insert_favorite_directory(self.unique_name, username)
        except:
            msg = f"Failed to set favorite for Directory '{self.unique_name}' and {username}"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the users's favorite directories.")
    
    def remove_favorite_directory(self, username:str) -> None:
        """
        Removes this directory from the favorites for a user. "Un-favorite".

        Args:
            username (str): The username to remove the directory from favorites for.

        Raises:
            UnsuccessfulAttributeUpdateException: If the directory cannot be removed from favorites.
        """
        try:
            with PACS_DB() as db:
                db.delete_favorite(self.unique_name, username)
        except:
            msg = f"Failed to un-favorite for Directory '{self.unique_name}' and {username}"
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the users's favorite directories.")

    def download(self, destination, zip: bool = True) -> str:
        """
        Downloads the contents of this directory.

        Args:
            destination (str): The destination folder for the download.
            zip (bool, optional): Whether to zip the downloaded contents. Defaults to True.

        Returns:
            str: The path to the downloaded contents.

        Raises:
            DownloadException: If the download fails.
        """
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
        """
        Helper method to create folders and copy files for download.

        Args:
            target_folder (str): The target folder for the download.

        Raises:
            DownloadException: If copying files for download fails.
        """
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
        Converts various attributes of the Directory object to a dictionary for serialization.

        Returns:
            dict: A dictionary representation of the directory.
        """
        return {
            'unique_name': self.unique_name,
            'display_name': self.display_name,
            'timestamp_creation': self.timestamp_creation.strftime("%d.%B %Y, %H:%M:%S"),
            'last_updated': self.last_updated.strftime("%d.%B %Y, %H:%M:%S"),     
            'is_consistent': self.is_consistent,   
            'parameters': self.parameters,
            'number_of_files': self.number_of_files,  
            'number_of_files_on_this_level': self.number_of_files_on_this_level,
            'associated_directory': self.parent_directory.unique_name if self.parent_directory else None,
            'associated_project': self.project.name,
            'user_rights': self.project.your_user_role,  
        }