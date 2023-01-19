import datetime
import json
import os
import pathlib
from tempfile import TemporaryDirectory
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union
import uuid
import zipfile

import requests


class XNAT():
    def __init__(self, server: str, username: str, password: str = None, session_id: str = None, kind: str = None) -> None:
        self.server = server
        self.username = username
        # User may either specify password of session_id to authenticate themselves
        if password != None:
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            # Authenticate user via REST API
            response = requests.post(
                server + "/data/services/auth", data=data, headers=headers)
            if response.status_code != 200:
                # Non successful authentication
                raise Exception(
                    "Something went wrong connecting to XNAT. " + str(response.text))
            else:
                # Return SessionID
                self.session_id = response.text
                self.cookies = {"JSESSIONID": self.session_id}
                # print(requests.get(self.server + "/xapi/users/username",cookies=self.cookies).text)
        elif session_id != None:
            self.session_id = session_id
            self.cookies = {"JSESSIONID": self.session_id}
        else:
            raise Exception(
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
            raise Exception("User not found." + str(response.status_code))

    def __enter__(self) -> 'XNAT':
        return self

    def __exit__(self, type, value, traceback) -> None:
        # TODO: invalidate Session_id
        pass

    def create_project(self, name: str) -> Optional['XNATProject']:
        headers = {'Content-Type': 'application/xml'}
        project_data = f"""
            <projectData>
            <ID>{name}</ID>
            <name>{name}</name>
            <description>This is a new project.</description>
            <keywords> Set keywords here. </keywords>
            </projectData>
            """
        response = requests.post(self.server + "/data/projects",
                                 headers=headers, data=project_data, cookies=self.cookies)
        if response.status_code == 200:
            return XNATProject(self, name)
        else:
            raise Exception(
                "Something went wrong trying to create a new project." + str(response.status_code))

    def get_project(self, name: str) -> Optional['XNATProject']:
        return XNATProject(self, name, only_get_no_create=True)

    def get_all_projects(self) -> List['XNATProject']:
        response = requests.get(
            self.server + "/xapi/users/projects", cookies=self.cookies)
        if response.status_code == 200:
            # Project list retrieval was successfull
            project_names = response.json()
            if len(project_names) == 0:
                # No projects yet
                return []

            projects = []
            for p in project_names:
                # Create List of all Project objectss
                project = self.get_project(p)
                projects.append(project)

            return projects
        else:
            # Project list not found
            raise Exception("Projects not found." + str(response.status_code))

    def get_directory(self, project_name: str, directory_name: str) -> Optional['XNATDirectory']:
        return XNATDirectory(self.get_project(project_name), directory_name)

#     def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
#         pass


class XNATProject():
    def __init__(self, connection: XNAT, name: str, only_get_no_create: bool = False) -> None:
        self.connection = connection
        self.server = self.connection.server
        self.cookies = self.connection.cookies
        self.name = name

        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}?format=json", cookies=self.cookies)
        if response.status_code == 200:
            # Project was successfully retrieved
            self._metadata = response.json()['items'][0]
        elif response.status_code != 200 and only_get_no_create is False:
            # No project could be retrieved -> we want to create one with the given name
            p = self.connection.create_project(self.name)
            self._metadata = p._metadata
        else:
            # No project could be retrieved and we do not wish to create one
            raise Exception(
                f"Project '{name}' not found." + str(response.status_code))

    @property
    def description(self) -> str:
        return self._metadata['data_fields']['description']

    def set_description(self, description_string: str) -> None:
        headers = {'Content-Type': 'application/xml'}
        project_data = f"""
            <projectData>
            <description>{description_string}</description>
            </projectData>
            """
        # Put new description
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}", headers=headers, data=project_data, cookies=self.cookies)
        if response.status_code == 200:
            self._metadata['data_fields']['description'] = description_string
        else:
            raise Exception(
                "Something went wrong trying to change the description string." + str(response.status_code))

    @property
    def keywords(self) -> str:
        return self._metadata['data_fields']['keywords']

    def set_keywords(self, keywords_string: str) -> None:
        headers = {'Content-Type': 'application/xml'}
        project_data = f"""
            <projectData>
            <keywords>{keywords_string}</keywords>
            </projectData>
            """
        # Put new keywords
        response = requests.put(
            self.connection.server + f"/data/projects/{self.name}", headers=headers, data=project_data, cookies=self.cookies)
        if response.status_code == 200:
            self._metadata['data_fields']['keywords'] = keywords_string
        else:
            raise Exception(
                "Something went wrong trying to change the keywords string. " + str(response.status_code))

    @property
    def owners(self) -> List[str]:
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.cookies)
        if response.status_code == 200:
            owners = []
            for o in response.json()['ResultSet']['Result']:
                if o['displayname'] == 'Owners':
                    owners.append(o['login'])
            return owners
        else:
            raise Exception(
                "Something went wrong trying to retrieve the owners of this project. " + str(response.status_code))

    @property
    def your_user_role(self) -> str:
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}/users", cookies=self.cookies)
        if response.status_code == 200:
            for o in response.json()['ResultSet']['Result']:
                if o['login'] == self.connection.user:
                    return o['displayname']
        else:
            raise Exception(
                "Something went wrong trying to retrieve your user role. " + str(response.status_code))

    def exists(self) -> bool:
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.cookies)
        if response.status_code == 200:
            return True
        else:
            return False

    def download(self, destination: str) -> str:
        pass

    def delete_project(self) -> None:
        response = requests.delete(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.cookies)
        if response.status_code != 200:
            raise Exception(
                'Something went wrong trying to delete the project.' + str(response.status_code))

    def get_directory(self, name) -> 'XNATDirectory':
        return XNATDirectory(self, name)

    def get_all_directories(self) -> Sequence['XNATDirectory']:
        response = requests.get(
            self.server + f"/data/projects/{self.name}/resources", cookies=self.cookies)
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

            return directories
        else:
            raise Exception(
                "No directories could be retrieved. " + str(response.status_code))

    def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['XNATDirectory', 'XNATFile']:
        # File path leads to a single file
        if os.path.isfile(file_path) and not zipfile.is_zipfile(file_path):
            return self.insert_file_into_project(file_path, directory_name, tags_string)

        # File path equals a zip file
        elif zipfile.is_zipfile(file_path):
            return self.insert_zip_into_project(file_path, directory_name, tags_string)

        else:
            raise Exception("The input is neither a file nor a zip.")

    def insert_zip_into_project(self, file_path: str, directory_name: str = '', tags_string='') -> 'XNATDirectory':
        # Extract zip data and feed it to insert_file_project
        if zipfile.is_zipfile(file_path):
            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                # This must be done here for zips bc otherwise all files end up in different directories
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            with TemporaryDirectory() as tempdir:
                with zipfile.ZipFile(file_path) as z:
                    z.extractall(tempdir)
                    dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])

                    # Get all files, even those within a lower-level directory
                    onlyfiles = []
                    for (dirpath, dirnames, filenames) in os.walk(dir_path):
                        onlyfiles.extend(filenames)

                    # Insert files
                    for f in onlyfiles:
                        self.insert_file_into_project(
                            os.path.join(dir_path, f), directory_name, tags_string)

            return XNATDirectory(self, directory_name)

        else:
            raise Exception("The input is not a zipfile.")

   # Single file upload to given project
    def insert_file_into_project(self, file_path: str, directory_name: str = '', tags_string: str = '') -> 'XNATFile':
        if os.path.exists(file_path):
            if directory_name == '':
                # If no xnat resource directory is given, a new directory with the current timestamp is created
                directory_name = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

            else:
                # XNAT can't handle whitespaces in names -> replace them with underscores
                directory_name = directory_name.replace(" ", "_")

            # Accepted File formats/suffixes
            allowed_file_suffixes = (
                '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff', '.csv', '.json')
            image_file_suffixes = (
                '.jpg', '.jpeg', '.png', '.nii', '.dcm', '.tiff')

            # File format metadata for the REST query parameter
            file_format = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.nii': 'NIFTI',
                           '.dcm': 'DICOM', '.tiff': 'TIFF', '.csv': 'CSV', '.json': 'JSON'}

            # Lowercase file_path so things like '.PNG' aren't a problem
            lower_file_path = file_path.lower()
            # Get the file's suffix
            suffix = pathlib.Path(lower_file_path).suffix

            # Only continue if file format/suffix is an accepted one 
            if suffix in allowed_file_suffixes:
                # File names are unique, duplicate file names can not be inserted
                file_id = str(uuid.uuid4())
                # Add file suffix to generated unique file_id
                file_id = file_id + suffix

                # Get correct content tag for REST query parameter
                if suffix in image_file_suffixes:
                    file_content = 'Image'
                else:
                    file_content = 'Metadata'

                # Update tags_string to include format, content and passed tags_string
                tags_string = f"{file_content}, {file_format[suffix]}, {tags_string}"

                # REST query parameter string to set metadata
                parameter = f"format={file_format[suffix]}&tags={tags_string}&content={file_content}"

                # Open passed file and POST to XNAT endpoint
                with open(file_path, "rb") as file:
                    response = requests.post(
                        self.server + f"/data/projects/{self.name}/resources/{directory_name}/files/{file_id}?{parameter}", files={'upload_file': file}, cookies=self.cookies)

                if response.status_code == 200:
                    # Return inserted file
                    return XNATFile(XNATDirectory(self, directory_name), file_id)
                else:
                    raise Exception(
                        f"The file [{self.name}] could not be uploaded. " + str(response.status_code))

            else:
                raise Exception("This file type is not supported.")

        else:
            raise Exception("The input is not a file.")


class XNATDirectory():
    def __init__(self, project: XNATProject, name: str) -> None:
        self.name = name
        self.project = project
        self.cookies = self.project.cookies
        self.server = self.project.server
        # Get all the projects directories, single GET is only possible for exists() (due to XNAT API behavior)
        response = requests.get(
            self.server + f"/data/projects/{self.project.name}/resources", cookies=self.cookies)
        if response.status_code == 200:
            all_dirs = response.json()['ResultSet']['Result']
            try:
                self._metadata = next(
                    item for item in all_dirs if item["label"] == self.name)
            except:
                raise Exception(
                    f"A Directory with this name ({self.name}) does not exist. ")
        else:
            raise Exception(
                f"Directories could not be accessed. " + str(response.status_code))

    @property
    def contained_file_tags(self) -> str:
        return self._metadata['tags']

    @property
    def number_of_files(self) -> str:
        return self._metadata['file_count']

    def exists(self) -> bool:
        response = requests.get(
            self.server + f"/data/projects/{self.project.name}/resources/{self.name}", cookies=self.cookies)
        if response.status_code == 200:
            return True
        else:
            return False

    def delete_directory(self) -> None:
        response = requests.delete(
            self.server + f"/data/projects/{self.project.name}/resources/{self.name}", cookies=self.cookies)
        if response.status_code != 200:
            raise Exception(
                "Something went wrong trying to delete this directory. " + str(response.status_code))

    def get_file(self, file_name: str) -> 'XNATFile':
        return XNATFile(self, file_name)

    def get_all_files(self) -> List['XNATFile']:
        response = requests.get(
            self.server + f"/data/projects/{self.project.name}/resources/{self.name}/files?format=json", cookies=self.cookies)
        if response.status_code == 200:
            # Directory list retrieval was successfull
            file_results = response.json()['ResultSet']['Result']
            if len(file_results) == 0:
                # No projects yet
                return []

            files = []
            for f in file_results:
                # Create List of all Project objectss
                file = self.get_file(f['Name'])
                files.append(file)

            return files
        else:
            raise Exception("No files could be retrieved. " +
                            str(response.status_code))

    def download(self, destination: str) -> str:
        pass


class XNATFile():
    def __init__(self, directory: XNATDirectory, name: str) -> None:
        self.directory = directory
        self.name = name
        self.cookies = self.directory.cookies
        self.server = self.directory.server

        response = requests.get(
            self.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files", cookies=self.cookies)
        if response.status_code == 200:
            all_files = response.json()['ResultSet']['Result']
            try:
                self._metadata = next(
                    item for item in all_files if item["Name"] == self.name)
            except:
                raise Exception(
                    f"A File with this filename ({self.name}) does not exist. ")
        else:
            raise Exception(
                f"Files could not be accessed. " + str(response.status_code))

    @property
    def format(self) -> str:
        return self._metadata['file_format']

    @property
    def content_type(self) -> str:
        return self._metadata['file_content']

    @property
    def tags(self) -> str:
        return self._metadata['file_tags']

    @property
    def size(self) -> int:
        return self._metadata['Size']

    @property
    def data(self) -> str:
        response = requests.get(
            self.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.cookies)
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(
                f"The file [{self.name}] could not be retrieved. " + str(response.status_code))

    def exists(self) -> bool:
        response = requests.get(
            self.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.cookies)
        if response.status_code == 200:
            True
        else:
            False

    def download(self, destination: str = '') -> str:
        pass

    def delete_file(self) -> None:
        response = requests.delete(
            self.server + f"/data/projects/{self.directory.project.name}/resources/{self.directory.name}/files/{self.name}", cookies=self.cookies)
        if response.status_code != 200:
            raise Exception(
                "Something went wrong trying to delete this file. " + str(response.status_code))
