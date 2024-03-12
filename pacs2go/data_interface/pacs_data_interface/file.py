from datetime import datetime

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulDeletionException,
    UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
#from pacs2go.data_interface.pacs_data_interface.directory import Directory as pacs_dir # only for typing, but creates circular import
from pacs2go.data_interface.xnat_rest_wrapper import XNATFile


class File:
    this_timezone = timezone("Europe/Berlin")

    def __init__(self, directory, name: str, _file_filestorage_object=None) -> None:
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
        try:
            return self._db_file.format
        except:
            msg = f"Failed to get format for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File format")

    @property
    def tags(self) -> str:
        try:
            return self._db_file.tags
        except:
            msg = f"Failed to get tags for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File tags")

    def set_tags(self, tags: str) -> None:
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
        try:
            return self._db_file.modality
        except:
            msg = f"Failed to get modality for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File modality")

    def set_modality(self, modality: str) -> None:
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
        try:
            return self._db_file.timestamp_creation
        except:
            msg = f"Failed to get creation timestamp for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File creation timestamp")

    @property
    def last_updated(self) -> str:
        try:
            return self._db_file.timestamp_last_updated
        except:
            msg = f"Failed to get last update timestamp for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File last update timestamp")

    def set_last_updated(self, timestamp: datetime) -> None:
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
        try:
            return self._file_store_file.content_type
        except:
            msg = f"Failed to get content type for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File content type")

    @property
    def size(self) -> int:
        try:
            return self._file_store_file.size
        except:
            msg = f"Failed to get size for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("File size")

    @property
    def data(self) -> bytes:
        try:
            return self._file_store_file.data
        except:
            msg = f"Failed to get file data for File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("The actual file data itself")

    def exists(self) -> bool:
        return self._file_store_file.exists()

    def download(self, destination: str = '') -> str:
        try:
            logger.info(f"User {self.directory.project.connection.user} downloaded File '{self.name}' from {self.directory.unique_name}.")
            return self._file_store_file.download(destination)
        except:
            msg = f"Failed to download File '{self.name}' in directory '{self.directory.unique_name}'."
            logger.exception(msg)
            raise DownloadException

    def delete_file(self) -> None:
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
        Convert various attributes of the File object to a dictionary for serialization.
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
