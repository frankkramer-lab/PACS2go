import os
from typing import List

import requests
from natsort import natsorted
from werkzeug.exceptions import Forbidden, HTTPException, NotFound

from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat.file import XNATFile
from pacs2go.data_interface.xnat.project import XNATProject

class XNATDirectory():
    """Represents a directory within an XNAT project."""
    
    def __init__(self, project: XNATProject, name: str) -> None:
        """
        Initializes an XNAT directory.

        Args:
            project (XNATProject): The project the directory belongs to.
            name (str): The name of the directory.

        Raises:
            HTTPException: If the directory cannot be accessed.
            NotFound: If the directory does not exist.
        """
        self.name = name
        self.project = project

        # Get all the projects directories, single GET is only possible for exists() (due to XNAT API behavior)
        response = requests.get(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources", cookies=self.project.connection.cookies)

        if not response.status_code == 200:
            msg = "Directories could not be accessed. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

        if not self.exists():
            raise NotFound

    def exists(self) -> bool:
        """
        Checks if the directory to this XNATDirectory object acutally exists on the XNAT server.

        Returns:
            bool: True if the directory exists, False otherwise.
        """
        response = requests.get(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources/{self.name}", cookies=self.project.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def delete_directory(self) -> None:
        """
        Deletes the directory from the project.

        Raises:
            Forbidden: If the user does not have permission to delete the directory. (Only project owner prevails these rights.)
            HTTPException: If the directory cannot be deleted.
        """
        response = requests.delete(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources/{self.name}", cookies=self.project.connection.cookies)

        if response.status_code == 403:
            # Note: In contrast to projects and files, double deleting the same resource still results in a 200 code
            msg = "Directories could not be accessed. " + str(response.status_code)
            logger.error(msg)
            raise Forbidden(
                "You're not allowed to delete directories of this project. Please contact a project owner. ")
        
        elif response.status_code != 200:
            msg = "Something went wrong trying to delete this directory. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def get_file(self, file_name: str, metadata: dict = None) -> 'XNATFile':
        """
        Retrieves a file by name from the directory.

        Args:
            file_name (str): The name of the file.
            metadata (dict, optional): Metadata for the file. Defaults to None.

        Returns:
            XNATFile: The retrieved file object.
        """
        return XNATFile(self, file_name, metadata)

    def get_all_files(self) -> List['XNATFile']:
        """
        Retrieves a list of all files in the directory.

        Returns:
            List[XNATFile]: A list of file objects.

        Raises:
            HTTPException: If the files cannot be retrieved.
        """
        response = requests.get(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources/{self.name}/files?format=json&sortBy=Name", cookies=self.project.connection.cookies)

        if response.status_code == 200:
            # Directory list retrieval was successfull
            file_results = response.json()['ResultSet']['Result']
            if len(file_results) == 0:
                # No files yet
                return []

            files = []
            for file in file_results:
                # Create List of all File objects
                file_object = self.get_file(file_name = file['Name'], metadata = file)
                files.append(file_object)
            files = natsorted(files, key=lambda obj: obj.name)

            return files

        else:
            msg = "No files could be retrieved. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def download(self, destination: str) -> str:
        """
        Downloads the directory as a zip file.

        Args:
            destination (str): The destination path to save the zip file.

        Returns:
            str: The path to the downloaded zip file.

        Raises:
            HTTPException: If the directory data cannot be downloaded.
        """
        # https://wiki.xnat.org/display/XAPI/How+To+Download+Files+via+the+XNAT+REST+API
        response = requests.get(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources/{self.name}/files?format=zip", cookies=self.project.connection.cookies)

        if response.status_code == 200:
            # Store the retrieved compressed archive (containing all files) in the specified destination
            path = os.path.join(destination, self.name + ".zip")
            with open(path, "wb") as binary_file:
                # Write zip bytes to file
                binary_file.write(response.content)
            return path

        else:
            msg = f"Something went wrong trying to download this directory {self.name}. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)


