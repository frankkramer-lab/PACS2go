from datetime import datetime

from pytz import timezone

from pacs2go.data_interface.data_structure_db import PACS_DB
from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulDeletionException,
    UnsuccessfulGetException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.pacs_data_interface.directory import Directory
from pacs2go.data_interface.xnat_rest_wrapper import XNATFile


timezone = timezone("Europe/Berlin")


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
            except:
                msg = f"Failed to get File '{name}' in directory '{self.directory.name}'."
                logger.exception(msg)
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
