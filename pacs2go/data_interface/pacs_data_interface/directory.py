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
from pacs2go.data_interface.pacs_data_interface.project import Project
from pacs2go.data_interface.xnat_rest_wrapper import XNATDirectory

# File format metadata
file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI',
               '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT'}

timezone = timezone("Europe/Berlin")

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
        except Exception:
            msg = f"Failed to get the number of files for Directory '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def parent_directory(self) -> 'Directory':
        try:
            if self._db_directory.parent_directory:
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
            self.project.set_last_updated(datetime.now(timezone))
            if self.parent_directory:
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
                    logger.info(f"insert {unique_name}")
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
            
            logger.debug(f"User {self.project.connection.user} retrieved information about subdirectories for directory '{self.name}'.")
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
            logger.debug(f"User {self.project.connection.user} retrieved information about all files for directory '{self.name}'.")
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
        except Exception:
            msg = f"Failed to copy files for download in directory '{self.name}'."
            logger.exception(msg)
            raise DownloadException

        for subdirectory in self.get_subdirectories():
            try:
                subdirectory._create_folders_and_copy_files_for_download(
                    current_folder)
            except Exception:
                msg = f"Failed to copy files for download in subdirectory '{subdirectory.name}' of directory '{self.name}'."
                logger.exception(msg)
                raise DownloadException