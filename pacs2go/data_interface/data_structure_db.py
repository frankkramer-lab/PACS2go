import os
from typing import List, NamedTuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, FailedDisconnectException)
from pacs2go.data_interface.tests.test_config import (DATABASE_HOST,
                                                      DATABASE_PORT)

load_dotenv()

class PACS_DB():
    def __init__(self, host:str = "data-structure-db", port:int=5432) -> None:
        try:
            # Connect to the Postgres service
            self.conn = psycopg2.connect(
                host=DATABASE_HOST,
                port=DATABASE_PORT,
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                database=os.getenv("POSTGRES_DB")
            )
            # Get cursor object to operate db
            self.cursor = self.conn.cursor()
        except:
            raise FailedConnectionException("No DB connection possible")

        # On inital setup create tables (all statements possess IF NOT EXISTS keyword)
        self.create_tables()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        try:
            self.cursor.close()
            self.conn.close()
        except:
            raise FailedDisconnectException("DB server disconnect was not successful.")

    # -------- Create Tables ------- #

    def create_tables(self):
        self.create_table_project()
        self.create_table_directory()
        self.create_table_citation()
        self.create_table_file()

    def create_table_project(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Project (
                    name VARCHAR(256) PRIMARY KEY,
                    keywords VARCHAR(256),
                    description VARCHAR(256),
                    parameters VARCHAR(256),
                    timestamp_creation TIMESTAMP,
                    timestamp_last_updated TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Project table could not be created. ")

    def create_table_directory(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Directory (
                    unique_name VARCHAR(256) PRIMARY KEY,
                    dir_name VARCHAR(256),
                    parent_project VARCHAR(256) REFERENCES Project(name) ON DELETE CASCADE,
                    parent_directory VARCHAR(256) REFERENCES Directory(unique_name) ON DELETE CASCADE,
                    timestamp_creation TIMESTAMP,
                    parameters VARCHAR(256),
                    timestamp_last_updated TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Directory table could not be created. ")
    
    def create_table_citation(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Citation (
                    cit_id SERIAL PRIMARY KEY,
                    citation VARCHAR(256),
                    link VARCHAR(256),
                    directory_unique_name VARCHAR(256) REFERENCES Directory(unique_name) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Citation table could not be created. ")

    def create_table_file(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS File (
                    file_name VARCHAR(256),
                    parent_directory VARCHAR(256) REFERENCES Directory(unique_name) ON DELETE CASCADE,
                    format VARCHAR(256),
                    tags VARCHAR(256),
                    modality VARCHAR(256),
                    timestamp_creation TIMESTAMP,
                    timestamp_last_updated TIMESTAMP,
                    PRIMARY KEY (file_name, parent_directory)
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("File table could not be created. ")


    # -------- Insert Into Tables ------- #

    def insert_into_project(self, data: 'ProjectData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Project (name, keywords, description, parameters, timestamp_creation, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data.name, data.keywords, data.description, data.parameters, data.timestamp_creation, data.timestamp_last_updated))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception(f"Error inserting {data.name} into Project table")

    def insert_into_directory(self, data: 'DirectoryData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Directory (unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data.unique_name, data.dir_name, data.parent_project, data.parent_directory, data.timestamp_creation, data.parameters, data.timestamp_last_updated))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception(f"Error inserting {data.dir_name} into Directory table")

    def insert_into_citation(self, data: 'CitationData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Citation (citation, link, directory_unique_name)
                VALUES (%s, %s, %s)
            """, (data.citation, data.link, data.directory_unique_name))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Error inserting into Citation table")

    def insert_into_file(self, data: 'FileData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO File (file_name, parent_directory, format, tags, modality, timestamp_creation, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data.file_name, data.parent_directory, data.format, data.tags, data.modality, data.timestamp_creation, data.timestamp_last_updated))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Error inserting into File table")
        
    def insert_multiple_files(self, files: List['FileData']) -> None:
        try:
            # Construct a list of tuples with (file_name, parent_directory) for each file
            file_values = [(file.file_name, file.parent_directory, file.format, file.tags, file.modality, file.timestamp_creation, file.timestamp_last_updated) for file in files]

            query = """
                INSERT INTO File (file_name, parent_directory, format, tags, modality, timestamp_creation, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_name) DO NOTHING
            """
            execute_values(self.cursor, query, file_values)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception(f"Error inserting multiple files")


    # -------- Select From Tables ------- #

    def get_all_projects(self) -> List['ProjectData']:
        try:
            query = """
                SELECT name, keywords, description, parameters, timestamp_creation, timestamp_last_updated
                FROM Project
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            project_list = []
            for row in results:
                project = ProjectData(*row)
                project_list.append(project)

            return project_list
        except Exception as err:
            print(err)
            raise Exception("Error retrieving all projects")

    def get_all_directories(self) -> List['DirectoryData']:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM Directory
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            directory_list = []
            for row in results:
                directory = DirectoryData(*row)
                directory_list.append(directory)

            return directory_list
        except Exception as err:
            print(err)
            raise Exception("Error retrieving all directories")

    def get_all_files(self) -> List[str]:
        try:
            query = """
                SELECT file_name FROM File
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            file_list = []
            for row in results:
                file_name = row[0]
                file_list.append(file_name)

            return file_list
        except Exception as err:
            raise Exception("Error retrieving all files")

    def get_project_by_name(self, project_name: str) -> 'ProjectData':
        try:
            query = """
                SELECT name, keywords, description, parameters, timestamp_creation, timestamp_last_updated
                FROM Project
                WHERE name = %s
            """
            self.cursor.execute(query, (project_name,))
            result = self.cursor.fetchone()

            if result:
                return ProjectData(*result)
            else:
                return None
        except Exception as err:
            print(err)
            raise Exception("Error retrieving project by name")        

    def get_directories_by_project(self, project_name: str) -> List['DirectoryData']:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM Directory
                WHERE parent_project = %s
            """
            self.cursor.execute(query, (project_name,))
            results = self.cursor.fetchall()

            directory_list = []
            for row in results:
                directory = DirectoryData(*row)
                directory_list.append(directory)

            return directory_list
        except Exception as err:
            print(err)
            raise Exception("Error retrieving directories by project")

    def get_directory_by_name(self, unique_name: str) -> 'DirectoryData':
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM Directory
                WHERE unique_name = %s
            """
            self.cursor.execute(query, (unique_name,))
            result = self.cursor.fetchone()

            if result:
                # Directory exists in the database
                return DirectoryData(*result)
            else:
                # Directory does not exist in the database
                return None
        except Exception as err:
            print(err)
            raise Exception("Error retrieving directory from the database")

    def get_subdirectories_by_directory(self, parent_directory: str) -> List['DirectoryData']:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM Directory
                WHERE parent_directory = %s
            """
            self.cursor.execute(query, (parent_directory,))
            results = self.cursor.fetchall()

            directory_list = []
            for row in results:
                directory = DirectoryData(*row)
                directory_list.append(directory)

            return directory_list
        except Exception as err:
            print(err)
            raise Exception("Error retrieving subdirectories by directory")


    # --------- Update Tables -------- #

    def update_attribute(self, table_name: str, attribute_name: str, new_value: str, condition_column: str = None, condition_value: str = None) -> None:
        try:
            if condition_column and condition_value:
                query = f"""
                    UPDATE {table_name}
                    SET {attribute_name} = %s
                    WHERE {condition_column} = %s
                """
                self.cursor.execute(query, (new_value, condition_value))
            else:
                query = f"""
                    UPDATE {table_name}
                    SET {attribute_name} = %s
                """
                self.cursor.execute(query, (new_value,))

            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception(f"Error updating {attribute_name} in {table_name}")

   # -------- Delete From Tables ------- #

    def delete_project_by_name(self, project_name: str) -> None:
        try:
            query = """
                DELETE FROM Project WHERE name = %s
            """
            self.cursor.execute(query, (project_name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Error deleting project by name")

    def delete_directory_by_name(self, unique_name: str) -> None:
        try:
            query = """
                DELETE FROM Directory WHERE unique_name = %s
            """
            self.cursor.execute(query, (unique_name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Error deleting directory by unique name")

    def delete_file_by_name(self, file_name: str) -> None:
        try:
            query = """
                DELETE FROM File WHERE file_name = %s
            """
            self.cursor.execute(query, (file_name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(err)
            raise Exception("Error deleting file by name")



# Named Tuples
class ProjectData(NamedTuple):
    name: str
    keywords: str
    description: str
    parameters: str
    timestamp_creation: str
    timestamp_last_updated: str

class DirectoryData(NamedTuple):
    unique_name: str
    dir_name: str
    parent_project: str
    parent_directory: str
    timestamp_creation: str
    parameters: str
    timestamp_last_updated: str

class CitationData(NamedTuple):
    cit_id: int
    citation: str
    link: str
    directory_unique_name: str

class FileData(NamedTuple):
    file_name: str
    parent_directory: str
    format: str
    tags: str
    modality: str
    timestamp_creation: str
    timestamp_last_updated: str


# with PACS_DB() as db:
#     # Retrieving all projects
#     projects = db.get_all_projects()
#     print("All Projects:")
#     for project_name in projects:
#         print(project_name)

#     # Retrieving all directories
#     directories = db.get_all_directories()
#     print("All Directories:")
#     for directory in directories:
#         print(directory)