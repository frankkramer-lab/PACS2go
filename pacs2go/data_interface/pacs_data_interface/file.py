from datetime import datetime

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulDeletionException,
    UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat import XNATFile


class File:
    """Represents a file within a directory in the PACS system, providing methods to manage file attributes and actions."""

    this_timezone = timezone("Europe/Berlin")

    def __init__(self, directory, name: str, _file_filestorage_object=None) -> None:
        """
        Initializes a File object.

        Args:
            directory (Directory): The directory to which this file belongs. (Not typed due to circular import.)
            name (str): The name of the file.
            _file_filestorage_object (optional): The file storage object. Defaults to None.

        Raises:
            UnsuccessfulGetException: If the file cannot be retrieved from the database or file storage.
            FailedConnectionException: If the connection type is unsupported.
        """
        self.directory = directory
        self.name = name

        try:
            with PACS_DB() as db:
                self._db_file = db.get_file_by_name_and_directory(
                    self.name, self.directory.unique_name)
                if self._db_file is None:
                    raise FileNotFoundError
        except:
            msg = f"Failed to get DB-File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"DB-File '{self.name}'")

        if _file_filestorage_object:
            self._file_store_file = _file_filestorage_object
        elif self.directory.project.connection._kind == "XNAT":
            try:
                self._file_store_file = XNATFile(directory._file_store_directory, self.name)
            except:
                msg = f"Failed to get File '{self.name}' in directory '{self.directory.unique_name}'."
                logger.exception(msg)
                raise UnsuccessfulGetException(f"File '{self.name}'")
        else:
            # FailedConnectionException because only these connection types are supported atm
            raise FailedConnectionException

    @property
    def format(self) -> str:
        """
        Returns the format (DICOM, JPEG, NIFTI,...) of the file.

        Returns:
            str: The file format.

        Raises:
            UnsuccessfulGetException: If the format cannot be retrieved.
        """
        try:
            return self._db_file.format
        except:
            msg = f"Failed to get format for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File format")

    @property
    def tags(self) -> str:
        """
        Returns the user-defined tags associated with the file.

        Returns:
            str: The user-defined file tags.

        Raises:
            UnsuccessfulGetException: If the tags cannot be retrieved.
        """
        try:
            return self._db_file.tags
        except:
            msg = f"Failed to get tags for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File tags")

    def set_tags(self, tags: str) -> None:
        """
        Sets the tags for the file.

        Args:
            tags (str): The new tags for the file.

        Raises:
            UnsuccessfulAttributeUpdateException: If the tags cannot be updated.
        """
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='File', attribute_name='tags', new_value=tags, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.unique_name)
            self.set_last_updated(datetime.now(self.this_timezone))
            logger.info(f"User {self.directory.project.connection.user} set tags for File '{self.name}' in directory '{self.directory.unique_name}' to '{tags}'.")
        except:
            msg = f"Failed to update tags for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'modality' to '{tags}'")

    @property
    def modality(self) -> str:
        """
        Returns the modality (MRI, CT,...) of the file.

        Returns:
            str: The file modality.

        Raises:
            UnsuccessfulGetException: If the modality cannot be retrieved.
        """
        try:
            return self._db_file.modality
        except:
            msg = f"Failed to get modality for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File modality")

    def set_modality(self, modality: str) -> None:
        """
        Sets the modality for the file.

        Args:
            modality (str): The new modality for the file.

        Raises:
            UnsuccessfulAttributeUpdateException: If the modality cannot be updated.
        """
        try:
            with PACS_DB() as db:
                db.update_attribute(
                    table_name='File', attribute_name='modality', new_value=modality, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.unique_name)
            self.set_last_updated(datetime.now(self.this_timezone))
            logger.info(f"User {self.directory.project.connection.user} set modality for File '{self.name}' in directory '{self.directory.unique_name}' to '{modality}'.")
        except:
            msg = f"Failed to update modality for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'modality' to '{modality}'")

    @property
    def timestamp_creation(self) -> str:
        """
        Returns the timestamp of the initial creation of the file.

        Returns:
            str: The creation timestamp.

        Raises:
            UnsuccessfulGetException: If the creation timestamp cannot be retrieved.
        """
        try:
            return self._db_file.timestamp_creation
        except:
            msg = f"Failed to get creation timestamp for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File creation timestamp")

    @property
    def last_updated(self) -> str:
        """
        Returns the last update timestamp of the file.

        Returns:
            str: The last update timestamp.

        Raises:
            UnsuccessfulGetException: If the last update timestamp cannot be retrieved.
        """
        try:
            return self._db_file.timestamp_last_updated
        except:
            msg = f"Failed to get last update timestamp for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File last update timestamp")

    def set_last_updated(self, timestamp: datetime) -> None:
        """
        Updates the last updated timestamp for the file.

        Args:
            timestamp (datetime): The new timestamp.

        Raises:
            UnsuccessfulAttributeUpdateException: If the timestamp cannot be updated.
        """
        try:
            with PACS_DB() as db:
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                db.update_attribute(
                    table_name='File', attribute_name='timestamp_last_updated', new_value=timestamp, condition_column='file_name',
                    condition_value=self.name, second_condition_column='parent_directory', second_condition_value=self.directory.unique_name)
        except:
            msg = f"Failed to update last_updated timestamp for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException(
                f"the file's 'last_updated' to '{timestamp}'")

    @property
    def content_type(self) -> str:
        """
        Returns the content type (Metadata / Image) of the file.

        Returns:
            str: The content type.

        Raises:
            UnsuccessfulGetException: If the content type cannot be retrieved.
        """
        try:
            return self._file_store_file.content_type
        except:
            msg = f"Failed to get content type for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File content type")

    @property
    def size(self) -> int:
        """
        Returns the Byte size of the file.

        Returns:
            int: The file size.

        Raises:
            UnsuccessfulGetException: If the size cannot be retrieved.
        """
        try:
            return self._file_store_file.size
        except:
            msg = f"Failed to get size for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File size")

    @property
    def data(self) -> bytes:
        """
        Returns the data of the file from the file store. 

        Returns:
            bytes: The file data.

        Raises:
            UnsuccessfulGetException: If the data cannot be retrieved.
        """
        try:
            return self._file_store_file.data
        except:
            msg = f"Failed to get file data for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("The actual file data itself")

    def exists(self) -> bool:
        """
        Checks if the file exists in the file store.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return self._file_store_file.exists()

    def download(self, destination: str = '') -> str:
        """
        Downloads the file to a specified destination.

        Args:
            destination (str, optional): The destination path. Defaults to ''.

        Returns:
            str: The path to the downloaded file.

        Raises:
            DownloadException: If the file cannot be downloaded.
        """
        try:
            logger.info(f"User {self.directory.project.connection.user} downloaded File '{self.name}' from {self.directory.unique_name}.")
            return self._file_store_file.download(destination)
        except:
            msg = f"Failed to download File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise DownloadException

    def delete_file(self) -> None:
        """
        Deletes the file from the file store and the database.

        Raises:
            UnsuccessfulDeletionException: If the file cannot be deleted.
        """
        try:
            self._file_store_file.delete_file()

            with PACS_DB() as db:
                db.delete_file_by_name(self.name, self.directory.unique_name)

            self.directory.set_last_updated(datetime.now(self.this_timezone))
            logger.info(f"User {self.directory.project.connection.user} deleted File '{self.name}' from {self.directory.unique_name}.")

        except:
            msg = f"Failed to delete File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulDeletionException(f"file '{self.name}'")



    def to_dict(self) -> dict:
        """
        Converts various attributes of the File object to a dictionary for serialization.

        Returns:
            dict: A dictionary representation of the file.
        """
        return {
            'name': self.name,
            'format': self.format,
            'modality': self.modality,
            'tags': self.tags,
            'size': self.size,
            'upload': self.timestamp_creation.strftime("%d.%B %Y, %H:%M:%S"),
            'last_updated': self.last_updated.strftime("%d.%B %Y, %H:%M:%S"),
            'associated_directory': self.directory.unique_name,
            'associated_project': self.directory.project.name,
            'user_rights': self.directory.project.your_user_role
        }
