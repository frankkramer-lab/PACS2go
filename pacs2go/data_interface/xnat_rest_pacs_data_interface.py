from typing import List
from typing import Optional
from typing import Sequence
from typing import Union

import requests


class XNAT():
    def __init__(self, server: str, username: str, password: str = None, session_id: str = None, kind: str = None) -> None:
        self.server = server
        self.username = username
        # User may either specify password of session_id to authenticate themselves
        if password != None:
            data = {"username": username, "password": password}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.post(
                server + "/data/services/auth", data=data, headers=headers)
            if response.status_code != 200:
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
            # User not found, return False
            raise Exception("User not found." + str(response.status_code))

    def __enter__(self) -> 'XNAT':
        return self

    def __exit__(self, type, value, traceback) -> None:
        # TODO: invalidate Session_id
        pass

    def create_project(self, name: str) -> Optional['XNATProject']:
        # A Project with the name 'name' does not exist yet, create one
        headers = {'Content-Type': 'application/xml'}
        project_data = f"""
            <projectData>
            <ID>{name}</ID>
            <name>{name}</name>
            <description>This is a new project.</description>
            </projectData>
            """
        response = requests.post(self.server + "/data/projects", headers=headers, data=project_data, cookies=self.cookies)
        if response.status_code == 200:
            print("Project created successfully")
            return XNATProject(self, name)
        else:
            raise Exception(
                "Something went wrong trying to create a new project." + str(response.status_code))

    def get_project(self, name: str) -> Optional['XNATProject']:
        response = requests.get(
            self.server + f"/data/projects/{name}", cookies=self.cookies)
        if response.status_code == 200:
            return XNATProject(self, name, just_get=True)
        else:
            # User not found, return False
            raise Exception(
                f"Project '{name}' not found." + str(response.status_code))

    def get_all_projects(self) -> List['XNATProject']:
        response = requests.get(
            self.server + "/xapi/users/projects", cookies=self.cookies)
        if response.status_code == 200:
            # User was found, return username
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
            # User not found, return False
            raise Exception("Projects not found." + str(response.status_code))

#     def get_directory(self, project_name: str, directory_name: str) -> Optional['Directory']:
#         pass

#     def get_file(self, project_name: str, directory_name: str, file_name: str) -> Optional['File']:
#         pass


class XNATProject():
    def __init__(self, connection: XNAT, name: str, just_get: bool = False) -> None:
        self.connection = connection
        self.cookies = self.connection.cookies
        self.name = name

        if just_get is False:
            # just_get is used to internally optimize the number of XNAT API calls
            response = requests.get(
                self.connection.server + f"/data/projects/{self.name}", cookies=self.cookies)
            if response.status_code != 200:
                # Project in XNAT does not exist yet, so it is inserted into XNAT
                self.connection.create_project(self.name)

    @property
    def description(self) -> str:
        response = requests.get(
            self.connection.server + f"/data/projects/{self.name}", cookies=self.cookies)
        if response.status_code == 200:
            return response.json()['description']
        else:
            raise Exception(
                'Something went wrong trying to retrieve the description' + str(response.status_code))

    def set_description(self, description_string: str) -> None:
        pass

    @property
    def keywords(self) -> str:
        pass

    def set_keywords(self, keywords_string: str) -> None:
        pass

    @property
    def owners(self) -> List[str]:
        pass

    @property
    def your_user_role(self) -> str:
        pass

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


#     def get_directory(self, name) -> 'Directory':
#         pass

#     def get_all_directories(self) -> Sequence['Directory']:
#         pass

#     def insert(self, file_path: str, directory_name: str = '', tags_string: str = '') -> Union['Directory', 'File']:
#         pass


# class Directory():
#     def __init__(self, project: Project, name: str) -> None:
#         pass

#     @property
#     def contained_file_tags(self) -> str:
#         pass

#     @property
#     def number_of_files(self) -> str:
#         pass

#     def exists(self) -> bool:
#         pass

#     def delete_directory(self) -> None:
#         pass

#     def get_file(self, file_name: str) -> 'File':
#         pass

#     def get_all_files(self) -> List['File']:
#         pass

#     def download(self, destination: str) -> str:
#         pass


# class File():
#     def __init__(self, directory: Directory, name: str) -> None:
#         pass

#     @property
#     def format(self) -> str:
#         pass

#     @property
#     def content_type(self) -> str:
#         pass

#     @property
#     def tags(self) -> str:
#         pass

#     @property
#     def size(self) -> int:
#         pass

#     @property
#     def data(self) -> str:
#         pass

#     def exists(self) -> bool:
#         pass

#     def download(self, destination: str = '') -> str:
#         pass

#     def delete_file(self) -> None:
#         pass
