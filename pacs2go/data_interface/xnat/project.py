import datetime
import os
import pathlib
import zipfile
from tempfile import TemporaryDirectory
from typing import List, Sequence, Union

import requests
from natsort import natsorted
from werkzeug.exceptions import Forbidden, HTTPException, NotFound

from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.xnat.utils.constants import allowed_file_suffixes, file_format, image_file_suffixes
from pacs2go.data_interface.xnat import XNAT


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

class XNATProject():
    """Represents a project on the XNAT server."""
    
    def __init__(self, connection: XNAT, name: str) -> None:
        """
        Initializes an XNAT project.

        Args:
            connection (XNAT): The XNAT connection.
            name (str): The name of the project.

        Raises:
            NotFound: If the project cannot be found.
        """
        self.connection = connection
        self.name = name
        
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}?format=json", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Project was successfully retrieved
            # Get returned metadata to optimize number of XNAT REST calls (description and keywords don't require extra call)
            self._metadata = response.json()['items'][0]

        else:
            # No project could be retrieved and we do not wish to create one
            msg = f"Project '{name}' not found." + str(response.status_code)
            logger.error(msg)
            raise NotFound(msg)

    @property
    def description(self) -> str:
        """
        Returns the description of the project.

        Returns:
            str: The project description.
        """
        return self._metadata['data_fields']['description']

    def set_description(self, description_string: str) -> None:
        """
        Sets the description of the project.

        Args:
            description_string (str): The new description.

        Raises:
            Forbidden: If the user does not have permission to change the description.
            HTTPException: If the description cannot be changed.
        """
        headers = {'Content-Type': 'application/xml'}

        # Specify metadata XML string
        project_data = f"""
            <projectData>
            <description>{description_string}</description>
            </projectData>
            """

        # Put new description
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}", headers=headers, data=project_data, cookies=self.connection.cookies)

        if response.status_code == 200:
            self._metadata['data_fields']['description'] = description_string
        elif response.status_code == 403:
            msg = "You do not possess the rights to change the project description."
            logger.error(msg)
            raise Forbidden(msg)
        else:
            msg = "Something went wrong trying to change the description string." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    @property
    def keywords(self) -> str:
        """
        Returns the keywords of the project.

        Returns:
            str: The project keywords.
        """
        return self._metadata['data_fields']['keywords']

    def set_keywords(self, keywords_string: str) -> None:
        """
        Sets the keywords of the project.

        Args:
            keywords_string (str): The new keywords.

        Raises:
            Forbidden: If the user does not have permission to change the keywords.
            HTTPException: If the keywords cannot be changed.
        """
        headers = {'Content-Type': 'application/xml'}

        # Specify project metadata XML string
        project_data = f"""
            <projectData>
            <keywords>{keywords_string}</keywords>
            </projectData>
            """

        # Put new keywords
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}", headers=headers, data=project_data, cookies=self.connection.cookies)

        if response.status_code == 200:
            self._metadata['data_fields']['keywords'] = keywords_string
        elif response.status_code == 403:
            msg = "You do not possess the rights to change the project keywords."
            logger.error(msg)
            raise Forbidden(msg)
        else:
            msg = "Something went wrong trying to change the keywords string." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    @property
    def owners(self) -> List[str]:
        """
        Returns the list of project owners.

        Returns:
            List[str]: A list of project owners.

        Raises:
            HTTPException: If the owners cannot be retrieved.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Retrieve only users with the role 'Owners'
            owners = []
            for element in response.json()['ResultSet']['Result']:
                if element['displayname'] == 'Owners':
                    owners.append(element['login'])
            return owners
        else:
            msg = "Something went wrong trying to retrieve the owners of this project." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    @property
    def members(self) -> List[str]:
        """
        Returns the list of project members.

        Returns:
            List[str]: A list of project members.

        Raises:
            HTTPException: If the members cannot be retrieved.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Retrieve only users with the role 'members'
            members = []
            for element in response.json()['ResultSet']['Result']:
                if element['displayname'] == 'Members':
                    members.append(element['login'])
            return members
        else:
            msg = "Something went wrong trying to retrieve the members of this project." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    @property
    def collaborators(self) -> List[str]:
        """
        Returns the list of project collaborators.

        Returns:
            List[str]: A list of project collaborators.

        Raises:
            HTTPException: If the collaborators cannot be retrieved.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Retrieve only users with the role 'collaborators'
            collaborators = []
            for element in response.json()['ResultSet']['Result']:
                if element['displayname'] == 'Collaborators':
                    collaborators.append(element['login'])
            return collaborators
        else:
            msg = "Something went wrong trying to retrieve the collaborators of this project." + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    @property
    def your_user_role(self) -> str:
        """
        Returns the user role of the authenticated user of this session in the project.

        Returns:
            str: The user role.

        Raises:
            HTTPException: If the user role cannot be retrieved.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Get the autheticated user's role in a project
            for element in response.json()['ResultSet']['Result']:
                if element['login'] == self.connection.user:
                    return str(element['displayname'])
            # User exists but no user role was specified
            return ''
        else:
            msg = "Something went wrong trying to retrieve your user role. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    def grant_rights_to_user(self, user: str, level: str) -> None:
        """
        Grants specific rights to a user in the project.

        Args:
            user (str): The username.
            level (str): The level of rights to grant.

        Raises:
            HTTPException: If the rights cannot be granted.
        """
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}/users/{level}/{user}", cookies=self.connection.cookies)
        if not response.status_code == 200:
            # Attention: the status code is 200 even if the user does not exist, bc originally the server then sends an invite to the stated email.
            msg = f"Something went wrong trying to add {user} to this project. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    def revoke_rights_from_user(self, user: str) -> None:
        """
        Revokes specific rights from a user in the project.

        Args:
            user (str): The username.

        Raises:
            HTTPException: If the rights cannot be revoked.
        """
        response = requests.delete(
            self.connection.server + f"/data/projects/{self.name}/users/Members/{user}", cookies=self.connection.cookies)
        response_2 = requests.delete(
            self.connection.server + f"/data/projects/{self.name}/users/Collaborators/{user}", cookies=self.connection.cookies)
        if not (response.status_code == 200 or response_2.status_code == 200):
            # Attention: the status code is 200 even if the user does not exist, bc originally the server then sends an invite to the stated email.
            msg = f"Something went wrong trying to remove {user} from this project. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)


    def exists(self) -> bool:
        """
        Checks if the project to this XNATProject object exists on the XNAT server.

        Returns:
            bool: True if the project exists, False otherwise.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def download(self, destination: str) -> str:
        """
        Downloads the project data as a zip file.

        Args:
            destination (str): The destination path to save the zip file.

        Returns:
            str: The path to the downloaded zip file.

        Raises:
            HTTPException: If the project data cannot be downloaded.
        """
        # Create a zip file for the project
        zip_destination = os.path.join(destination, f'{self.name}.zip')

        with TemporaryDirectory() as tempdir:
            # Iterate over directories to download them and write them to the project zip
            for d in self.get_all_directories():
                directory_filename = d.download(tempdir)

                with zipfile.ZipFile(zip_destination, 'a') as zip:
                    zip.write(directory_filename, os.path.relpath(
                        directory_filename, tempdir))

        return zip_destination

    def delete_project(self) -> None:
        """
        Deletes the project from the XNAT server.

        Raises:
            Forbidden: If the user does not have permission to delete the project. (Only project "owners" are able to delete their project.)
            HTTPException: If the project cannot be deleted.
        """
        response = requests.delete(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.connection.cookies)

        if response.status_code == 403:
            msg = 'You do not possess the rights to delete this project. Please contact a project owner. ' + str(response.status_code)
            logger.error(msg)
            raise Forbidden(msg)
        elif response.status_code != 200:
            msg = 'Something went wrong trying to delete the project.' + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)
        
    def create_directory(self, name) -> 'XNATDirectory': # type: ignore
        """
        Creates a new directory within the project.

        Args:
            name (str): The name of the directory.

        Returns:
            XNATDirectory: The created directory object.
        """
        # To create an empty directory in XNAT, it is necessary to temporarily insert a file.
        file_path = 'empty_directory_initialization_file.txt'
        with open(file_path, 'w') as f:
            f.write('No content')
        
        file = self.insert(file_path=file_path,directory_name=name)
        dir = file.directory
        
        if self.your_user_role == 'Owners':
            file.delete_file()

        os.remove(file_path)
        return dir

    def get_directory(self, name) -> 'XNATDirectory': # type: ignore
        from pacs2go.data_interface.xnat import XNATDirectory
        """
        Retrieves a directory by name from the project.

        Args:
            name (str): The name of the directory.

        Returns:
            XNATDirectory: The retrieved directory object.
        """
        return XNATDirectory(self, name)

    def get_all_directories(self) -> Sequence['XNATDirectory']: # type: ignore
        """
        Retrieves a list of all directories in the project.

        Returns:
            Sequence[XNATDirectory]: A list of directory objects.

        Raises:
            HTTPException: If the directories cannot be retrieved.
        """
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/resources?sortBy=label", cookies=self.connection.cookies)

        if response.status_code == 200:
            # Directory list retrieval was successfull
            dir_results = response.json()['ResultSet']['Result']
            if len(dir_results) == 0:
                # No projects yet
                return []

            directories = []
            for d in dir_results:
                # Create List of all Project objectss
                directory = self.get_directory(d['label'])
                directories.append(directory)

            directories = natsorted(directories, key=lambda obj: obj.name)
            return directories

        else:
            msg = "No directories could be retrieved. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['XNATDirectory', 'XNATFile']: # type: ignore
        """
        Inserts a file or a directory (for zip files) from a file path into the project.

        Args:
            file_path (str): The path to the (zip) file.
            directory_name (str, optional): The name of the directory to insert into. Defaults to ''.
            tags_string (str, optional): Tags associated with the file. Defaults to ''.

        Returns:
            Union[XNATDirectory, XNATFile]: The inserted directory or file object.

        Raises:
            ValueError: If the input format is not supported.
        """
        # File path leads to a single file
        if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
            return self.insert_file_into_project(file_path=file_path, directory_name=directory_name, tags_string=tags_string)

        # File path equals a zip file
        elif zipfile.is_zipfile(file_path):
            return self.insert_zip_into_project(file_path, directory_name, tags_string)

        else:
            msg = "Wrong input format"
            logger.error(msg)
            raise ValueError("The input is neither a file nor a zip.")

    def insert_zip_into_project(self, file_path: str, directory_name: str = '', tags_string: str = '', zip_extraction: bool = True, xnat_compressed_upload: bool = False) -> 'XNATDirectory': # type: ignore
        from pacs2go.data_interface.xnat import XNATDirectory
        """
        Inserts a zip file into the project.

        Args:
            file_path (str): The path to the zip file.
            directory_name (str, optional): The name of the directory to insert into. Defaults to ''.
            tags_string (str, optional): Tags associated with the file. Defaults to ''.
            zip_extraction (bool, optional): Flag to extract the zip file. Defaults to True.
            xnat_compressed_upload (bool, optional): Flag to use compressed upload. Defaults to False.

        Returns:
            XNATDirectory: The directory object created from the zip file.

        Raises:
            ValueError: If the input is not a zip file.
            HTTPException: If the file cannot be uploaded.
        """
        # Extract zip data and feed it to insert_file_project
        if zipfile.is_zipfile(file_path):
            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                # This must be done here for zips bc otherwise all files end up in different directories
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            if tags_string == '':
                tags_string = 'No tags'
            cookies=self.connection.cookies
            
            ##### Dirty Workaround to create legit cookies for Member user role (see issue #35) ####
            if self.your_user_role == 'Members':
                data = {"username": os.getenv("XNAT_USER"), "password": os.getenv("XNAT_PASS")}
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                # Authenticate 'user' via REST API
                response_fake_auth = requests.post(
                self.connection.server + "/data/services/auth", data=data, headers=headers)
                cookies = {"JSESSIONID": response_fake_auth.text}
            ########

            if xnat_compressed_upload:
                # Open passed file and POST to XNAT endpoint with compressed upload (files will be extracted automatically)
                with open(file_path, "rb") as file:
                    response = requests.post(
                        self.connection.server + f"/data/projects/{self.name}/resources/{directory_name}/files?extract={zip_extraction}&tags={tags_string}", files={'file.zip': file}, cookies=cookies)

                if response.status_code == 200:
                    # Return inserted file
                    return XNATDirectory(self, directory_name)
                else:
                    raise HTTPException(
                        f"The file [{self.name}] could not be uploaded. " + str(response.status_code))

            else:
                # Not using the xnat compressed upload means all files are extracted and uploaded individually including content_type and file format
                with TemporaryDirectory() as tempdir:
                    with zipfile.ZipFile(file_path) as z:
                        z.extractall(tempdir)
                        with os.scandir(tempdir) as entries:
                            dir_path = next(entries).path

                        # Get all files, even those within a lower-level directory
                        onlyfiles = []
                        for (dirpath, dirnames, filenames) in os.walk(dir_path):
                            onlyfiles.extend(filenames)

                        # Insert files
                        for f in onlyfiles:
                            self.insert_file_into_project(
                                file_path=os.path.join(dir_path, f), directory_name=directory_name, tags_string=tags_string)

                return XNATDirectory(self, directory_name)

        else:
            raise ValueError("The input is not a zipfile.")

    # Single file upload to given project
    def insert_file_into_project(self, file_path: str, file_id:str='', directory_name: str = '', tags_string: str = '') -> 'XNATFile': # type: ignore
        from pacs2go.data_interface.xnat import XNATDirectory, XNATFile
        """
        Inserts a single file into the project.

        Args:
            file_path (str): The path to the file.
            file_id (str, optional): The ID of the file. Defaults to ''.
            directory_name (str, optional): The name of the directory to insert into. Defaults to ''.
            tags_string (str, optional): Tags associated with the file. Defaults to ''.

        Returns:
            XNATFile: The inserted file object.

        Raises:
            ValueError: If the file type is not supported or the input is not a file.
            HTTPException: If the file cannot be uploaded.
        """
        if os.path.exists(file_path):
            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            # Lowercase file_path so things like '.PNG' aren't a problem
            lower_file_path = file_path.lower()
            # Get the file's suffix
            suffix = pathlib.Path(lower_file_path).suffix

            # Only continue if file format/suffix is an accepted one
            if suffix in allowed_file_suffixes:
                # Get unique file name 
                if file_id == '':
                    file_id = file_path.split("/")[-1]

                # Get correct content tag for REST query parameter
                if suffix in image_file_suffixes:
                    file_content = 'Image'
                else:
                    file_content = 'Metadata'

                # Update tags_string to include format, content and passed tags_string
                tags_string = f"{file_content}, {file_format[suffix]}, {tags_string}"

                # REST query parameter string to set metadata
                parameter = f"format={file_format[suffix]}&tags={tags_string}&content={file_content}"

                cookies = self.connection.cookies

                ##### (Dirty) Workaround to create legit cookies for Member user role (see issue #35) ####
                if self.your_user_role == 'Members':
                    data = {"username": os.getenv('XNAT_USER'), "password": os.getenv('XNAT_PASS')}
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}
                    # Authenticate 'user' via REST API
                    response_fake_auth = requests.post(
                    self.connection.server + "/data/services/auth", data=data, headers=headers)
                    cookies = {"JSESSIONID": response_fake_auth.text}
                ########

                # Open passed file and POST to XNAT endpoint
                with open(file_path, "rb") as file:
                    response = requests.post(
                            self.connection.server + f"/data/projects/{self.name}/resources/{directory_name}/files/{file_id}?{parameter}", files={'upload_file': file}, cookies=cookies)

                if response.status_code == 200:
                    # Return inserted file
                    return XNATFile(XNATDirectory(self, directory_name), file_id)
                else:
                    msg = f"The file [{self.name}] could not be uploaded. " + str(response.status_code)
                    logger.error(msg)
                    raise HTTPException(msg)

            else:
                raise ValueError("This file type is not supported.")

        else:
            raise ValueError("The input is not a file.")
