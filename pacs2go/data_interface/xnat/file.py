import os

import requests
from werkzeug.exceptions import Forbidden, HTTPException, NotFound

from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat import XNATDirectory
from pacs2go.data_interface.xnat.utils import file_format, image_file_suffixes

class XNATFile():
    """Represents a file within an XNAT directory."""
    
    def __init__(self, directory: XNATDirectory, name: str, metadata:dict = None) -> None:
        """
        Initializes an XNAT file object.

        Args:
            directory (XNATDirectory): The directory the file belongs to.
            name (str): The name of the file.
            metadata (dict, optional): Metadata for the file. Defaults to None.

        Raises:
            HTTPException: If the file metadata cannot be retrieved.
            NotFound: If the file does not exist.
        """
        self.directory = directory
        self.name = name

        if metadata:
            # Format etc will be passed in case of the Directory's get_all_files method, this will speed up the metadata extraction process
            self._metadata = metadata
        else:
            # Get all files from this file's directory (retrieving the metadata of a single file via a GET is not possible)
            response = requests.get(
                self.directory.project.connection.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files", cookies=self.directory.project.connection.cookies)

            if response.status_code == 200:
                all_files = response.json()['ResultSet']['Result']
                try:
                    # Find correct file and extract metadata
                    self._metadata = next(
                        item for item in all_files if item["Name"] == self.name)
                except:
                    msg = f"A File with this filename ({self.name}) does not exist. "
                    logger.error(msg)
                    raise NotFound(msg)
            else:
                msg = "Files could not be accessed. " + str(response.status_code)
                logger.error(msg)
                raise HTTPException(msg)

    @property
    def format(self) -> str:
        """
        Returns the format of the file.

        Returns:
            str: The file format.
        """
        if self._metadata['file_format'] != '':
            # If file format is either passed or stored in XNAT
            return self._metadata['file_format']
        elif "." in self.name:
            # Retrieve information from file name
            extension = "." + self.name.split(".")[-1]
            return file_format.get(extension.lower(), "Unknown")
        else:
            return 'N/A'

    @property
    def content_type(self) -> str:
        """
        Returns the content type of the file.

        Returns:
            str: The file content type.
        """
        if self._metadata['file_content'] != '':
            # If content type is either passed or stored in XNAT
            return self._metadata['file_content']
        elif "." in self.name:
            # Retrieve information from file name
            extension = "." + self.name.split(".")[-1]
            if extension in image_file_suffixes:
                return 'Image'
            else:
                return 'Metadata'
        else:
            return 'N/A'

    @property
    def tags(self) -> str:
        """
        Returns the tags associated with the file.

        Returns:
            str: The file tags.
        """
        if self._metadata['file_tags'] != '':
            return self._metadata['file_tags']
        else:
            return 'No tags'

    @property
    def size(self) -> int:
        """
        Returns the size of the file in bytes.

        Returns:
            int: The file size.
        """
        return int(self._metadata['Size'])

    @property
    def data(self) -> bytes:
        """
        Returns the data of the file as bytes.

        Returns:
            bytes: The file data.

        Raises:
            HTTPException: If the file data cannot be retrieved.
        """
        # Uses retrieved URI as endpoint
        # Useful for xnat compressed uploads where endpoint contains more than just filename (folders etc)
        # Example: '/data/projects/8412ac46-3752-4c3a-a2e1-73d9fa63e9e5_test1/resources/1118/files/jpegs_25/Case-3-A14-39214-1868.jpg'
        response = requests.get(
            self.directory.project.connection.server + self._metadata['URI'], cookies=self.directory.project.connection.cookies)

        if response.status_code == 200:
            # Return bytes
            return bytes(response.content)
        else:
            msg = f"The file data for [{self.name}] could not be retrieved. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def exists(self) -> bool:
        """
        Checks if the file to this file object actually exists on this XNAT server.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        response = requests.get(
            self.directory.project.connection.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.directory.project.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def download(self, destination: str = '') -> str:
        """
        Downloads the file.

        Args:
            destination (str, optional): The destination path to save the file. Defaults to ''.

        Returns:
            str: The path to the downloaded file.

        Raises:
            HTTPException: If the file cannot be downloaded.
        """
        response = requests.get(
            self.directory.project.connection.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.directory.project.connection.cookies)

        if response.status_code == 200:
            path = os.path.join(destination, self.name)
            with open(path, "wb") as binary_file:
                # Write bytes to file
                binary_file.write(response.content)
            return path
        else:
            msg = "Download was not possible." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def delete_file(self) -> None:
        """
        Deletes the file from the directory.

        Raises:
            Forbidden: If the user does not have permission to delete the file. (Only project owner prevails these rights.)
            HTTPException: If the file cannot be deleted.
        """
        response = requests.delete(
            self.directory.project.connection.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.directory.project.connection.cookies)

        if response.status_code == 403:
            msg = "You're not allowed to delete files of this project. Please contact a project owner. " + str(response.status_code)
            logger.error(msg)
            raise Forbidden(msg)
        elif response.status_code != 200:
            msg = "Something went wrong trying to delete this file. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)