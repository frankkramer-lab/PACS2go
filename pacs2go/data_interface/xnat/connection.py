import json
from typing import List

import requests
from werkzeug.exceptions import HTTPException

from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat import XNATProject, XNATDirectory, XNATFile
from pacs2go.data_interface.xnat.file import XNATFile
from pacs2go.data_interface.xnat.project import XNATProject

# Accepted File formats/suffixes
allowed_file_suffixes = (
    '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff', '.csv', '.json', '.txt', '.pdf', '.gz', '.json', '.gif', '.md', '.py', '.ipynb', '.svg')
image_file_suffixes = (
    '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff', '.gif', '.gz' '.svg')

# File format metadata
file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI', '.gz' : 'compressed NIFTI',
               '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT', '.gif':'GIF',
               '.json': 'JSON', '.pdf': 'PDF', '.md':'Markdown', '.py':'Python File', '.ipynb': 'Interactive Python Notebook',
               '.svg':'Scalable Vector Graphics'}


class XNAT():
    """Represents an XNAT connection, providing methods to interact with the XNAT server."""

    def __init__(self, server: str, username: str, password: str = '', session_id: str = '') -> None:
        """
        Initializes an XNAT connection.

        Args:
            server (str): The URL of the XNAT server, e.g.: http://localhost:8888.
            username (str): The username for authentication, e.g.: admin.
            password (str, optional): The password for authentication. Defaults to ''.
            session_id (str, optional): The session ID for authentication. Defaults to ''.

        Raises:
            HTTPException: If authentication fails or required parameters are not provided.
        """
        self.server = server
        self.username = username

        # User may either specify password of session_id to authenticate themselves
        if password:
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            # Authenticate user via REST API
            response = requests.post(
                server + "/data/services/auth", data=data, headers=headers)

            if response.status_code != 200:
                # Non successful authentication
                msg = f"No connection to XNAT possible: {response.status_code}"
                logger.error(msg)
                raise HTTPException(
                    "Something went wrong connecting to XNAT. " + str(response.status_code))
            else:
                # Return SessionID
                self.session_id = response.text
                self.cookies = {"JSESSIONID": self.session_id}
                # Log successful authentication
                logger.info(f"User authenticated successfully. {requests.get(self.server + '/xapi/users/username',cookies=self.cookies).text}")

        elif session_id:
            self.session_id = session_id
            self.cookies = {"JSESSIONID": self.session_id}
        else:
            raise ValueError(
                "You must eiter specify a password or a session_id to authenticate.")

    @property
    def _kind(self) -> str:
        """Returns the type of connection. In case of this wrapper this is always XNAT"""
        return "XNAT"

    @property
    def user(self) -> str:
        """
        Retrieves the currently authenticated username for this session.

        Returns:
            str: The authenticated username.

        Raises:
            HTTPException: If the username cannot be retrieved.
        """
        response = requests.get(
            self.server + "/xapi/users/username", cookies=self.cookies)

        if response.status_code == 200:
            # User was found, return username
            return response.text
        else:
            # User not found
            msg = "User not found."
            logger.error(msg)
            raise HTTPException(msg + str(response.status_code))
        
    @property
    def all_users(self) -> list:
        """
        Retrieves a list of all users of this XNAT server.

        Returns:
            list: A list of all users.

        Raises:
            HTTPException: If the user list cannot be retrieved.
        """
        response = requests.get(
            self.server + "/xapi/users", cookies=self.cookies)

        if response.status_code == 200:
            # users were found, return list of users
            user_list = json.loads(response.text)
            return user_list
        else:
            # User not found
            msg = "User list not found."
            logger.error(msg)
            raise HTTPException(msg + str(response.status_code))
        
    def heartbeat(self):
        """
        Checks if the session is still valid. Additionally keeps the session alive when called.

        Raises:
            HTTPException: If the session is invalid.
        """
        response = requests.get(
            self.server + "/data/JSESSION/", cookies=self.cookies)
        if response.status_code != 200:
            # If 200 isn't returned this means that the jsessionid has been invalidated (timeout)
            raise HTTPException("Unauthorized")
        else:
            return response     

    def __enter__(self) -> 'XNAT':
        """Enters the context for the XNAT connection."""
        return self

    def __exit__(self, type, value, traceback) -> None:
        """
        Exits the context for the XNAT connection, invalidating the session.

        Raises:
            HTTPException: If the session cannot be invalidated.
        """
        response = requests.post(
            self.server + "/data/JSESSION/", cookies=self.cookies)
        if response.status_code != 200:
            msg = "Unable to invalidate session Id."
            logger.error(msg)
            raise HTTPException(msg + str(response.status_code))        
        else:
            logger.info("XNAT session was successfully invalidated.")

    def create_project(self, name: str, description: str = '', keywords:str = '') -> 'XNATProject':
        """
        Creates a new project on the XNAT server.

        Args:
            name (str): The name of the to-be-created project. Has to be unique.
            description (str, optional): The description of the project. Defaults to ''.
            keywords (str, optional): The keywords for the project. Defaults to ''.

        Returns:
            XNATProject: The created project object.

        Raises:
            HTTPException: If the project cannot be created.
        """
        headers = {'Content-Type': 'application/xml'}
        # Specify XML metadata
        project_data = f"""
            <projectData>
            <ID>{name}</ID>
            <name>{name}</name>
            <description>{description if description else 'This is a new project.'}</description>
            <keywords>{keywords if keywords else 'Set keywords here.'}</keywords>
            </projectData>
            """
        response = requests.post(self.server + "/data/projects",
                                 headers=headers, data=project_data, cookies=self.cookies)
        if response.status_code == 200:
            # If successful return XNATProject object
            return XNATProject(self, name)
        else:
            msg = "Something went wrong trying to create a new project." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    def get_project(self, name: str) -> 'XNATProject':
        """
        Retrieves a project by name.

        Args:
            name (str): The name of the project.

        Returns:
            XNATProject: The retrieved project object.
        """
        return XNATProject(self, name)

    def get_all_projects(self) -> List['XNATProject']:
        """
        Retrieves a list of all projects.

        Returns:
            List[XNATProject]: A list of all project objects.

        Raises:
            HTTPException: If the projects cannot be retrieved.
        """
        response = requests.get(
            self.server + "/xapi/access/projects", cookies=self.cookies)

        if response.status_code == 200:
            # Project list retrieval was successfull
            project_names = response.json()
            if len(project_names) == 0:
                # No projects yet
                return []

            projects = []
            for p in project_names:
                # Create List of all Project objectss
                if 'name' in p:
                    project = self.get_project(p['name'])
                    projects.append(project)

            return projects
        else:
            # Project list not found
            msg = "Projects not found." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def get_directory(self, project_name: str, directory_name: str) -> 'XNATDirectory':
        """
        Retrieves a directory by name from a project.

        Args:
            project_name (str): The name of the project.
            directory_name (str): The name of the directory.

        Returns:
            XNATDirectory: The retrieved directory object.
        """
        return XNATDirectory(self.get_project(project_name), directory_name)

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> 'XNATFile':
        """
        Retrieves a file by name from a directory in a project.

        Args:
            project_name (str): The name of the project.
            directory_name (str): The name of the directory.
            file_name (str): The name of the file.

        Returns:
            XNATFile: The retrieved file object.
        """
        return XNATFile(XNATDirectory(XNATProject(self, project_name), directory_name), file_name)