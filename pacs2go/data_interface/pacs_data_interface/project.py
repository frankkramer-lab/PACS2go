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
from pacs2go.data_interface.pacs_data_interface.directory import Directory
from pacs2go.data_interface.pacs_data_interface.file import File
from pacs2go.data_interface.xnat import XNATProject


class Project:
    """Represents a project within the PACS system, providing methods to manage directories, files, and project attributes."""

    # File format metadata
    file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI', '.gz' : 'compressed (NIFTI)',
                '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT', '.gif':'GIF',
                '.json': 'JSON', '.pdf': 'PDF', '.md':'Markdown', '.py':'Python File', '.ipynb': 'Interactive Python Notebook', 
                '.svg':'Scalable Vector Graphics'}

    this_timezone = timezone("Europe/Berlin")

    def __init__(self, connection, name: str, _project_file_store_object=None) -> None:
        """
        Initializes a Project object.

        Args:
            connection (Connection): The connection to the PACS system. (Not typed due to circular import.)
            name (str): The name of the project.
            _project_file_store_object (optional): The project file storage object. Defaults to None and will be retrieved here. Specification leads to optimized performance.

        Raises:
            UnsuccessfulGetException: If the project cannot be retrieved from the database or file storage.
            FailedConnectionException: If the connection type is unsupported.
        """
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
        """
        Returns the description of the project.

        Returns:
            str: The project description.

        Raises:
            UnsuccessfulGetException: If the description cannot be retrieved.
        """
        try:
            return self._db_project.description
        except:
            msg = f"Failed to get Project description from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project description")

    def set_description(self, description_string: str) -> None:
        """
        Sets the description of the project.

        Args:
            description_string (str): The new description for the project.

        Raises:
            UnsuccessfulAttributeUpdateException: If the description cannot be updated.
        """
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
        """
        Returns the user-specified keywords associated with the project.

        Returns:
            str: The project keywords.

        Raises:
            UnsuccessfulGetException: If the keywords cannot be retrieved.
        """
        try:
            return self._db_project.keywords
        except:
            msg = f"Failed to get Project-related keywords from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project-related keywords")

    def set_keywords(self, keywords_string: str) -> None:
        """
        Updates/Overwrites the keywords for the project. 

        Args:
            keywords_string (str): The new keywords for the project.

        Raises:
            UnsuccessfulAttributeUpdateException: If the keywords cannot be updated.
        """
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
        """
        Returns the user-specified parameters associated with the project.

        Returns:
            str: The project parameters.

        Raises:
            UnsuccessfulGetException: If the parameters cannot be retrieved.
        """
        try:
            return self._db_project.parameters
        except:
            msg = f"Failed to get Project-related parameters from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project-related parameters")

    def set_parameters(self, parameters_string: str) -> None:
        """
        Sets/Overwrites the parameters for the project.

        Args:
            parameters_string (str): The new parameters for the project.

        Raises:
            UnsuccessfulAttributeUpdateException: If the parameters cannot be updated.
        """
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
        """
        Returns the last updated timestamp of the project.

        Returns:
            datetime: The last updated timestamp.

        Raises:
            UnsuccessfulGetException: If the timestamp cannot be retrieved.
        """
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
        """
        Sets the last updated timestamp for the project.

        Args:
            timestamp (datetime): The new timestamp.

        Raises:
            UnsuccessfulAttributeUpdateException: If the timestamp cannot be updated.
        """
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
        """
        Returns the timestamp of the intial creation of the project.

        Returns:
            datetime: The creation timestamp.

        Raises:
            UnsuccessfulGetException: If the timestamp cannot be retrieved.
        """
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
    def number_of_directories(self) -> int:
        """
        Returns the number of directories in the project. (Direct children.)

        Returns:
            int: The number of directories.

        Raises:
            UnsuccessfulGetException: If the number of directories cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                return db.get_numberofdirectories_in_project(self.name)
            
        except Exception:
            msg = f"Failed to get the number of directories for Project '{self.name}'"
            logger.exception(msg)
            raise UnsuccessfulGetException(msg)

    @property
    def owners(self) -> List[str]:
        """
        Returns the list of owners of the project. Types of user roles: Owners, Members, Collaborators. See XNAT documentation for explaination.

        Returns:
            List[str]: The list of project owners.

        Raises:
            UnsuccessfulGetException: If the owners cannot be retrieved.
        """
        try:
            return self._file_store_project.owners
        except:
            msg = f"Failed to get the list of Project owners from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "Project users that are assigned an 'owner' role")
    
    @property
    def members(self) -> List[str]:
        """
        Returns the list of members of the project.

        Returns:
            List[str]: The list of project members.

        Raises:
            UnsuccessfulGetException: If the members cannot be retrieved.
        """
        try:
            return self._file_store_project.members
        except:
            msg = f"Failed to get the list of Project members from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "Project users that are assigned a 'members' role")
        
    @property
    def collaborators(self) -> List[str]:
        """
        Returns the list of collaborators of the project.

        Returns:
            List[str]: The list of project collaborators.

        Raises:
            UnsuccessfulGetException: If the collaborators cannot be retrieved.
        """
        try:
            return self._file_store_project.collaborators
        except:
            msg = f"Failed to get the list of Project collaborators from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(
                "Project users that are assigned a 'collaborators' role")

    @property
    def your_user_role(self) -> str:
        """
        Returns the user role of the current user in the project.

        Returns:
            str: The user role. Either Owners, Members, Collaborators or an empty string.

        Raises:
            UnsuccessfulGetException: If the user role cannot be retrieved.
        """
        try:
            return self._file_store_project.your_user_role
        except:
            msg = f"Failed to get your user role from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Your user role")

    def grant_rights_to_user(self, user: str, level: str) -> None:
        """
        Grants specific rights to a user in the project. Only Owners and admin have rights to perform this action.

        Args:
            user (str): The username.
            level (str): The level of rights to grant.

        Raises:
            UnsuccessfulAttributeUpdateException: If the rights cannot be granted.
        """
        try:
            self._file_store_project.grant_rights_to_user(user, level)
            self.remove_request(user)
        except Exception as err:
            msg = f"Failed to add user {user} to Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException("new user" + str(err))
        
    def revoke_rights_from_user(self, user: str) -> None:
        """
        Revokes specific rights from a user in the project.

        Args:
            user (str): The username.

        Raises:
            UnsuccessfulAttributeUpdateException: If the rights cannot be revoked.
        """
        try:
            self._file_store_project.revoke_rights_from_user(user)
            self.remove_request(user)
        except Exception as err:
            msg = f"Failed to remove user {user} from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException("Removing user" + str(err))
        
    def add_request(self, user:str) -> None:
        """
        Adds a request from a user to join the project. Owners may resolve these requests.

        Args:
            user (str): The username.

        Raises:
            UnsuccessfulAttributeUpdateException: If the request cannot be added.
        """
        try:
            with PACS_DB() as db:
                db.insert_request_to_project(self.name, user)
                
        except:
            msg = f"Failed to add request for user {user} and Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException("New request")
    
    def remove_request(self, user:str) -> None:
        """
        Removes a request from a user to join the project.

        Args:
            user (str): The username.

        Raises:
            UnsuccessfulAttributeUpdateException: If the request cannot be removed.
        """
        try:
            with PACS_DB() as db:
                db.delete_request(self.name, user)
                
        except:
            msg = f"Failed to remove request for user {user} and Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulAttributeUpdateException("Removing request")
    
    def get_requests(self) -> list:
        """
        Retrieves the list of requests (list of usernames) to join the project.

        Returns:
            list: The list of usernames that requested access to the project.

        Raises:
            UnsuccessfulGetException: If the requests cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                return db.get_requests_to_project(self.name)

        except:
            msg = f"Failed to get requests for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Project requests")

    @property
    def citations(self) -> List['CitationData']:
        """
        Returns the list of citations associated with the project.

        Returns:
            List[CitationData]: The list of citations (containing id, citation string, link).

        Raises:
            UnsuccessfulGetException: If the citations cannot be retrieved.
        """
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
        """
        Adds a citation to the project.

        Args:
            citations_string (str): The citation string.
            link (str): The link to the citation.

        Raises:
            UnsuccessfulAttributeUpdateException: If the citation cannot be added.
        """
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
        """
        Removes a citation from the project.

        Args:
            citation_id (int): The ID of the citation.

        Raises:
            UnsuccessfulDeletionException: If the citation cannot be deleted.
        """
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
        """
        Checks if the project exists in the file store.

        Returns:
            bool: True if the project exists, False otherwise.
        """
        return self._file_store_project.exists()

    def download(self, destination: str) -> str:
        """
        Downloads the project data to a specified destination.

        Args:
            destination (str): The destination path.

        Returns:
            str: The path to the downloaded project data.

        Raises:
            DownloadException: If the project data cannot be downloaded.
        """
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
        """
        Deletes the project and all related data from the database and file store.

        Raises:
            UnsuccessfulDeletionException: If the project cannot be deleted.
        """
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
        """
        Creates a new directory within the project. (Only direct children, for subdirectories use create_subdirectory from Directory.)

        Args:
            unique_name (str): The unique name for the directory.
            parameters (str, optional): Additional parameters for the directory. Defaults to None.

        Returns:
            Tuple: A tuple containing the file store directory and the database directory object.

        Raises:
            UnsuccessfulCreationException: If the directory cannot be created.
        """
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

    def get_directory(self, name) -> 'Directory':
        """
        Retrieves a directory by name from the project.

        Args:
            name (str): The name of the directory.

        Returns:
            Directory: The retrieved directory instance.

        Raises:
            UnsuccessfulGetException: If the directory cannot be retrieved.
        """
        try:
            logger.debug(
                f"User {self.connection.user} retrieved information about directory '{name}' for Project '{self.name}'.")
            return Directory(self, name=name)
        except:
            msg = f"Failed to get Directory '{name}' from Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException(f"Directory '{name}'")

    def get_all_directories(self, filter:str= None, offset:int = None, quantity:int = None) -> Sequence['Directory']:
        """
        Retrieves a list of all directories in the project. Offset and Quantity are utilized for pagination optimization.

        Args:
            filter (str, optional): Filter for directory retrieval. Defaults to None.
            offset (int, optional): Offset for directory retrieval. Defaults to None.
            quantity (int, optional): Quantity of directories to retrieve. Defaults to None.

        Returns:
            Sequence[Directory]: A list of directory objects.

        Raises:
            UnsuccessfulGetException: If the directories cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                directories_from_db = db.get_directories_by_project(self.name, filter, offset, quantity)

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
    
    def get_all_directory_names_including_subdirectories(self) -> list:
        """
        Retrieves a list of all directory names, including subdirectories, in the project.

        Returns:
            list: A list of directory names.

        Raises:
            UnsuccessfulGetException: If the directory names cannot be retrieved.
        """
        try:
            with PACS_DB() as db:
                directories_from_db = db.get_all_directories_including_subdirectories_by_project(self.name)
            
            directory_names = [d.unique_name for d in directories_from_db]
            return directory_names

        except:
            msg = f"Failed to get a list of all directory names for Project '{self.name}'."
            logger.exception(msg)
            raise UnsuccessfulGetException("Directory names")

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '', modality: str = '', unpack_directly:bool = False) -> Union['Directory', 'File']:
        """
        Inserts a file (or a directory folder if zip) from a file path into the project.

        Args:
            file_path (str): The path to the file or directory.
            directory_name (str, optional): The name of the directory to insert into. Defaults to ''.
            tags_string (str, optional): Tags associated with the file(s). Defaults to ''.
            modality (str, optional): The modality of the file(s). Defaults to ''.
            unpack_directly (bool, optional): Whether to unpack the directory directly. If true, no new directory will be created but the files will be unpacked to the specified directory. Defaults to False.

        Returns:
            Union[Directory, File]: The inserted directory or file instance.

        Raises:
            WrongUploadFormatException: If the file format is not supported.
            UnsuccessfulUploadException: If the file or directory cannot be uploaded.
            UnsuccessfulCreationException: If the directory cannot be created.
        """
        try:
            timestamp = datetime.now(self.this_timezone).strftime("%Y-%m-%d %H:%M:%S")

            # File path leads to a single file
            if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
                if directory_name == '':
                    # No desired name was given, set the name as the current timestamp
                    directory_name = datetime.now(
                        self.this_timezone).strftime("%Y_%m_%d_%H_%M_%S")

                parent_dir = None if directory_name.count('::') < 2 else self.get_directory(directory_name.rsplit('::', 1)[0])
                directory = Directory(self, directory_name, parent_dir=parent_dir)
           
                with PACS_DB() as db:
                    # Get the file's suffix
                    format = self.file_format[Path(file_path).suffix.lower()]
                    size = Path(file_path).stat().st_size
                    file_id = file_path.split("/")[-1]
                    # Insert file into DB
                    updated_file_data = db.insert_into_file(
                        FileData(file_name=file_id, parent_directory=directory.unique_name, timestamp_creation=timestamp, timestamp_last_updated=timestamp, format=format, size=size, modality=modality, tags=tags_string))

                # Upload file to file store
                file_store_file_object = self._file_store_project.insert_file_into_project(
                    file_path=file_path, file_id=updated_file_data.file_name, directory_name=directory.unique_name, tags_string=tags_string)

                self.set_last_updated(datetime.now(self.this_timezone))
                logger.info(
                    f"User {self.connection.user} inserted a file '{file_store_file_object.name}' into Directory '{directory.unique_name}' in Project '{self.name}'.")
                return File(directory=directory, name=file_store_file_object.name, _file_filestorage_object=file_store_file_object)

            # File path equals a zip file
            elif zipfile.is_zipfile(file_path):
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Unzip the file to the temporary directory
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)


                    # Use the first directory inside the zip as the root directory
                    first_level_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)) and d != "__MACOSX"]
                    if len(first_level_dirs) > 1:
                        msg = f"Unexpected zip form: '{file_path}' has {len(first_level_dirs)} top level directory, a zip file is expected to have just one."
                        logger.exception(msg)
                        raise WrongUploadFormatException(msg, str(file_path.split("/")[-1]))
                    
                    logger.info(f"User {self.connection.user} has begun to upload {file_path}, top level directory is: {first_level_dirs}")

                    root_dir_name = first_level_dirs[0]
                    
                    # If directory was choosen, work there else directly under project (parent_dir=none)
                    parent_dir = None if directory_name=='' or directory_name.count('::') < 1 else self.get_directory(directory_name)
                    if parent_dir is not None and unpack_directly:
                        # For direct unpack do not create extra directory
                        root_dir = parent_dir
                    else:
                        # NO direct unpack, so create new directory for zipped folder (top level folder)
                        directory = Directory(self, root_dir_name, parent_dir=parent_dir)
                        root_dir = directory

                    # Start with the root directory
                    current_dir = root_dir
                    # Keep track of current depth
                    depth = 0
                    
                    
                    # Walk through the unzipped directory
                    for root, dirs, files in os.walk(temp_dir):  
                        try:
                            if root == temp_dir or "__MACOSX" in root:
                                # Skip tempdir name and skip top level folder for direct unpack, skip mac specific 
                                continue
                        
                            if not (os.path.basename(root) == root_dir.display_name or (unpack_directly and os.path.basename(root)==root_dir_name)):
                                # Only increase nesting level if root path implies that you should (This way directories of the same level stay on the same level)
                                if root.count(os.sep) != depth:
                                    directory = current_dir
                                    depth = root.count(os.sep)
                              
                                # Create sub-directory according to zipfile
                                current_dir = Directory(self, os.path.basename(root), parent_dir=directory)
                                
                            if len(files) > 0:
                                # Handle files of current directory
                                for file_name in files:

                                    if Path(file_name).suffix == '' or file_name.startswith("._"):
                                        # Skip files that do not have a file extension or are zipping artefacts
                                        logger.info(
                                            f"User {self.connection.user} tried to insert a forbidden file ('{file_name}') into Directory '{directory.unique_name}' in Project '{self.name}'.")
                                        continue

                                    # Create a FileData object
                                    file_data = FileData(
                                        file_name=file_name,
                                        parent_directory=current_dir.unique_name,
                                        format=self.file_format[Path(file_name).suffix.lower()],
                                        size=Path(os.path.join(root, file_name)).stat().st_size,
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
                                        # logger.info(f"insert {updated_file_data.file_name}, {updated_file_data.parent_directory}") # only for debugging as it is very time consuming

                                    # Upload to file store
                                    self._file_store_project.insert_file_into_project(
                                        file_path=os.path.join(root, file_name), file_id=updated_file_data.file_name, directory_name=current_dir.unique_name, tags_string=tags_string)
                           
                        except Exception as e:
                            logger.exception(f"An error occurred while processing files: {e}")
                            continue
                        
  
                    self.set_last_updated(datetime.now(self.this_timezone))
                    logger.info(
                        f"User {self.connection.user} inserted a zip file into Directory '{root_dir.unique_name}' in Project '{self.name}'.")
                    
                return root_dir

            else:
                raise ValueError
        
        except UnsuccessfulCreationException as err:
            raise Exception(err)
            
        except ValueError:
            msg = f"File format not supported for file path: '{file_path}'."
            logger.exception(msg)
            raise WrongUploadFormatException(str(file_path.split("/")[-1]))
        
        except Exception:
            msg = f"Failed to insert a file into Project '{self.name}' from file path: '{file_path}'."
            logger.exception(msg)
            raise UnsuccessfulUploadException(str(file_path.split("/")[-1]))


    def to_dict(self) -> dict:
        """
        Converts various attributes of the Project object to a dictionary for serialization.

        Returns:
            dict: A dictionary representation of the project.
        """
        return {
            'name': self.name,
            'timestamp_creation': self.timestamp_creation.strftime("%d.%B %Y, %H:%M:%S"),
            'last_updated': self.last_updated.strftime("%d.%B %Y, %H:%M:%S"),     
            'description': self.description,   
            'keywords': self.keywords,   
            'parameters': self.parameters,
            'number_of_directories': self.number_of_directories,
            'citations': [{'cit_id':c.cit_id, 'citation':c.citation, 'link':c.link} for c in self.citations],     
            'your_user_role': self.your_user_role,
            'owners': self.owners,   
            'members': self.members,   
            'collaborators': self.collaborators,   
            'requestees': self.get_requests()
        }