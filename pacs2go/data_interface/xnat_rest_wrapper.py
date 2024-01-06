import datetime
import json
import os
import pathlib
import uuid
import zipfile
from tempfile import TemporaryDirectory
from typing import List, Sequence, Union

import requests
from natsort import natsorted
from werkzeug.exceptions import Forbidden, HTTPException, NotFound

from pacs2go.data_interface.logs.config_logging import logger

# Accepted File formats/suffixes
allowed_file_suffixes = (
    '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff', '.csv', '.json', '.txt')
image_file_suffixes = (
    '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff')

# File format metadata
file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI',
               '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON', '.txt': 'TXT'}


class XNAT():
    def __init__(self, server: str, username: str, password: str = '', session_id: str = '', kind: str = '') -> None:
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
        return "XNAT"

    @property
    def user(self) -> str:
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

    def __enter__(self) -> 'XNAT':
        return self

    def __exit__(self, type, value, traceback) -> None:
        response = requests.post(
            self.server + "/data/JSESSION/", cookies=self.cookies)
        if response.status_code != 200:
            msg = "Unable to invalidate session Id."
            logger.error(msg)
            raise HTTPException(msg + str(response.status_code))        
        else:
            logger.info("XNAT session was successfully invalidated.")

    def create_project(self, name: str, description: str = '', keywords:str = '') -> 'XNATProject':
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
        return XNATProject(self, name, only_get_no_create=True)

    def get_all_projects(self) -> List['XNATProject']:
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
        return XNATDirectory(self.get_project(project_name), directory_name)

    def get_file(self, project_name: str, directory_name: str, file_name: str) -> 'XNATFile':
        return XNATFile(XNATDirectory(XNATProject(self, project_name), directory_name), file_name)


class XNATProject():
    def __init__(self, connection: XNAT, name: str, only_get_no_create: bool = False) -> None:
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
        return self._metadata['data_fields']['description']

    def set_description(self, description_string: str) -> None:
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
        return self._metadata['data_fields']['keywords']

    def set_keywords(self, keywords_string: str) -> None:
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
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}/users/{level}/{user}", cookies=self.connection.cookies)
        if not response.status_code == 200:
            # Attention: the status code is 200 even if the user does not exist, bc originally the server then sends an invite to the stated email.
            msg = f"Something went wrong trying to add {user} to this project. " + str(response.status_code)
            logger.error(msg)
            raise HTTPException(msg)


    def exists(self) -> bool:
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def download(self, destination: str) -> str:
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
        
    def create_directory(self, name) -> 'XNATDirectory':
        # To create an empty directory in XNAT, it is necessary to temporarily insert a file.
        file_path = 'empty_dir.txt'
        with open(file_path, 'w') as f:
            f.write('No content')
        
        file = self.insert(file_path=file_path,directory_name=name)
        dir = file.directory
        file.delete_file()
        os.remove(file_path)
        return dir

    def get_directory(self, name) -> 'XNATDirectory':
        return XNATDirectory(self, name)

    def get_all_directories(self) -> Sequence['XNATDirectory']:
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

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['XNATDirectory', 'XNATFile']:
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

    def insert_zip_into_project(self, file_path: str, directory_name: str = '', tags_string: str = '', zip_extraction: bool = True, xnat_compressed_upload: bool = False) -> 'XNATDirectory':
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
    def insert_file_into_project(self, file_path: str, file_id:str='', directory_name: str = '', tags_string: str = '') -> 'XNATFile':
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

                ##### Dirty Workaround to create legit cookies for Member user role (see issue #35) ####
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


class XNATDirectory():
    def __init__(self, project: XNATProject, name: str) -> None:
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
        response = requests.get(
            self.project.connection.server + f"/data/projects/{self.project.name}/resources/{self.name}", cookies=self.project.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def delete_directory(self) -> None:
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
        return XNATFile(self, file_name, metadata)

    def get_all_files(self) -> List['XNATFile']:
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


class XNATFile():
    def __init__(self, directory: XNATDirectory, name: str, metadata:dict = None) -> None:
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
        if self._metadata['file_tags'] != '':
            return self._metadata['file_tags']
        else:
            return 'No tags'

    @property
    def size(self) -> int:
        return int(self._metadata['Size'])

    @property
    def data(self) -> bytes:
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
        response = requests.get(
            self.directory.project.connection.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.directory.project.connection.cookies)

        if response.status_code == 200:
            return True
        else:
            return False

    def download(self, destination: str = '') -> str:
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
