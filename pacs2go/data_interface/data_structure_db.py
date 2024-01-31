import os
from typing import List, NamedTuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, FailedDisconnectException)
from pacs2go.data_interface.logs.config_logging import logger
from pacs2go.data_interface.tests.test_config import (DATABASE_HOST,
                                                      DATABASE_PORT)

load_dotenv()

class PACS_DB():
    # Define table names as constants
    PROJECT_TABLE = "Project"
    DIRECTORY_TABLE = "Directory"
    CITATION_TABLE = "Citation"
    FILE_TABLE = "File"
    FAVORITE_TABLE = "FavoriteDirectories"

    def __init__(self, host: str = "data-structure-db", port: int = 5432) -> None:
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
            # logger.info("DB connection established")
        except:
            msg = "No DB connection possible."
            logger.exception(msg)
            raise FailedConnectionException(msg)

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
            msg = "DB server disconnect was not successful."
            logger.exception(msg)
            raise FailedDisconnectException(msg)

    # -------- Create Tables ------- #

    def create_tables(self):
        self.create_table_project()
        self.create_table_directory()
        self.create_table_citation()
        self.create_table_file()
        self.create_table_favorite_directories()

    def create_table_project(self):
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.PROJECT_TABLE} (
                    name VARCHAR(256) PRIMARY KEY,
                    keywords VARCHAR(256),
                    description VARCHAR(256),
                    parameters VARCHAR(1024),
                    timestamp_creation TIMESTAMP,
                    timestamp_last_updated TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Project table could not be created. "
            logger.exception(msg)
            raise Exception(msg)

    def create_table_directory(self):
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.DIRECTORY_TABLE} (
                    unique_name VARCHAR(256) PRIMARY KEY,
                    dir_name VARCHAR(256),
                    parent_project VARCHAR(256) REFERENCES {self.PROJECT_TABLE}(name) ON DELETE CASCADE,
                    parent_directory VARCHAR(256) REFERENCES {self.DIRECTORY_TABLE}(unique_name) ON DELETE CASCADE,
                    timestamp_creation TIMESTAMP,
                    parameters VARCHAR(1024),
                    timestamp_last_updated TIMESTAMP
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Directory table could not be created."
            logger.exception(msg)
            raise Exception(msg)

    def create_table_citation(self):
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.CITATION_TABLE} (
                    cit_id SERIAL PRIMARY KEY,
                    citation VARCHAR(512),
                    link VARCHAR(512),
                    project_name VARCHAR(256) REFERENCES {self.PROJECT_TABLE}(name) ON DELETE SET NULL
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Citation table could not be created."
            logger.exception(msg)
            raise Exception(msg)
        
    def create_table_file(self):
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.FILE_TABLE} (
                    file_name VARCHAR(256),
                    parent_directory VARCHAR(256) REFERENCES {self.DIRECTORY_TABLE}(unique_name) ON DELETE CASCADE,
                    format VARCHAR(256),
                    size DECIMAL,
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
            msg = "File table could not be created."
            logger.exception(msg)
            raise Exception(msg)
    
    def create_table_favorite_directories(self):
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.FAVORITE_TABLE} (
                    fav_id SERIAL PRIMARY KEY,
                    directory VARCHAR(256) REFERENCES {self.DIRECTORY_TABLE}(unique_name) ON DELETE CASCADE,
                    username VARCHAR(128)
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "FavoriteDirectories table could not be created."
            logger.exception(msg)
            raise Exception(msg)
            
    # -------- Insert Into Tables ------- #

    def insert_into_project(self, data: 'ProjectData') -> None:
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.PROJECT_TABLE} (name, keywords, description, parameters, timestamp_creation, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (data.name, data.keywords, data.description, data.parameters, data.timestamp_creation, data.timestamp_last_updated))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"Error inserting {data.name} into Project table"
            logger.exception(msg)
            raise Exception(msg)

    def insert_into_directory(self, data: 'DirectoryData') -> None:
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.DIRECTORY_TABLE} (unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data.unique_name, data.dir_name, data.parent_project, data.parent_directory, data.timestamp_creation, data.parameters, data.timestamp_last_updated))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"Error inserting {data.dir_name} into Directory table"
            logger.exception(msg)
            raise Exception(msg)

    def insert_into_citation(self, data: 'CitationData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Citation (citation, link, project_name)
                VALUES (%s, %s, %s)
            """, (data.citation, data.link, data.project_name))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Error inserting into Citation table"
            logger.exception(msg)
            raise Exception(msg)

    def insert_into_file(self, data: 'FileData') -> 'FileData':
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.FILE_TABLE} (file_name, parent_directory, format, size, tags, modality, timestamp_creation, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (data.file_name, data.parent_directory, data.format, data.size, data.tags, data.modality, data.timestamp_creation, data.timestamp_last_updated))
            self.conn.commit()
            return data
        except psycopg2.IntegrityError as e:
            # Check if the error message contains "duplicate key value violates unique constraint"
            if "duplicate key value violates unique constraint" in str(e):
                self.conn.rollback()
                # Create a new instance of FileData with the updated file_name
                data = self.get_next_available_file_data(data)
                # Retry the insertion
                self.insert_into_file(data)
                # Return updated data with a new name
                return data
            else:
                # Handle other IntegrityError cases
                self.conn.rollback()
                msg = "Error inserting into File table"
                logger.exception(msg)
                raise Exception(msg)
        except Exception as err:
            self.conn.rollback()
            msg = "Error inserting into File table"
            logger.exception(msg)
            raise Exception(msg)

    def insert_multiple_files(self, files: List['FileData']) -> None:
        try:
            # Construct a list of tuples with (file_name, parent_directory) for each file
            file_values = [(file.file_name, file.parent_directory, file.format, file.tags,
                            file.modality, file.timestamp_creation, file.timestamp_last_updated) for file in files]
            query = f"""
                INSERT INTO {self.FILE_TABLE} (file_name, parent_directory, format, size, tags, modality, timestamp_creation, timestamp_last_updated)
                VALUES %s
            """
            execute_values(self.cursor, query, file_values)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = "Error inserting multiple files"
            logger.exception(msg)
            raise Exception(msg)

    def insert_favorite_directory(self, directory, username) -> None:
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.FAVORITE_TABLE} (directory, username)
                VALUES (%s, %s)
            """, (directory, username))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"Error inserting into {self.FAVORITE_TABLE} table"
            logger.exception(msg)
            raise Exception(msg)

    # -------- Select From Tables ------- #

    def get_all_projects(self) -> List['ProjectData']:
        try:
            query = f"""
                SELECT name, keywords, description, parameters, timestamp_creation, timestamp_last_updated
                FROM {self.PROJECT_TABLE}
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            project_list = []
            for row in results:
                project = ProjectData(*row)
                project_list.append(project)

            return project_list
        except Exception as err:
            msg = "Error retrieving all projects"
            logger.exception(msg)
            raise Exception(msg)

    def get_all_directories(self) -> List['DirectoryData']:
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            directory_list = []
            for row in results:
                directory = DirectoryData(*row)
                directory_list.append(directory)

            return directory_list
        except Exception as err:
            msg = "Error retrieving all directories"
            logger.exception(msg)
            raise Exception(msg)

    def get_all_files(self, directory_name:str) -> List[str]:
        try:
            query = f"""
                SELECT file_name FROM {self.FILE_TABLE} 
                WHERE parent_directory = %s
            """  
            self.cursor.execute(query, (directory_name,))
            results = self.cursor.fetchall()

            file_list = []
            for row in results:
                file_name = row[0]
                file_list.append(file_name)

            return file_list
        except Exception as err:
            msg = "Error retrieving all files"
            logger.exception(msg)
            raise Exception(msg)

    def get_directory_files_slice(self, directory_name:str, filter:str = '', quantity:int = None, offset:int = 0) -> List['FileData']:
            # quantity defines the number of retrievd files, offset defines how many rows are skipped before the retrieved files
            query = f"""
                SELECT file_name, parent_directory, format, size, tags, modality, timestamp_creation, timestamp_last_updated FROM {self.FILE_TABLE}
                WHERE parent_directory = %s AND (tags ILIKE %s OR file_name ILIKE %s)
                ORDER BY file_name 
                OFFSET %s ROWS
                FETCH FIRST %s ROW ONLY;
            """    
            self.cursor.execute(query, (directory_name,f'%{filter}%', f'%{filter}%', offset, quantity))
            results = self.cursor.fetchall()
            
            file_list = []
            for row in results:
                file = FileData(*row)
                file_list.append(file)
   
            return file_list


    def get_project_by_name(self, project_name: str) -> 'ProjectData':
        try:
            query = f"""
                SELECT name, keywords, description, parameters, timestamp_creation, timestamp_last_updated
                FROM {self.PROJECT_TABLE}
                WHERE name = %s
            """
            self.cursor.execute(query, (project_name,))
            result = self.cursor.fetchone()

            if result:
                return ProjectData(*result)
            else:
                return None
        except Exception as err:
            msg = "Error retrieving project by name"
            logger.exception(msg)
            raise Exception(msg)

    def get_directories_by_project(self, project_name: str) -> List['DirectoryData']:
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
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
            msg = "Error retrieving directories by project"
            logger.exception(msg)
            raise Exception(msg)

    def get_directory_by_name(self, unique_name: str) -> 'DirectoryData':
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
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
            msg = "Error retrieving directory from the database"
            logger.exception(msg)
            raise Exception(msg)

    def get_file_by_name_and_directory(self, file_name: str, parent_directory: str) -> 'FileData':
        try:
            query = f"""
                SELECT file_name, parent_directory, format, size, tags, modality, timestamp_creation, timestamp_last_updated
                FROM {self.FILE_TABLE}
                WHERE file_name = %s AND parent_directory = %s
            """
            self.cursor.execute(query, (file_name, parent_directory))
            result = self.cursor.fetchone()

            if result:
                # File exists in the database
                return FileData(*result)
            else:
                # File does not exist in the database
                return None
        except Exception as err:
            msg = "Error retrieving file from the database"
            logger.exception(msg)
            raise Exception(msg)

    def get_subdirectories_by_directory(self, parent_directory: str) -> List['DirectoryData']:
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
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
            msg = "Error retrieving subdirectories by directory"
            logger.exception(msg)
            raise Exception(msg)

    def get_citations_for_project(self, project_name: str) -> List['CitationData']:
        try:
            query = """
                SELECT cit_id, citation, link, project_name
                FROM Citation
                WHERE project_name = %s
            """
            self.cursor.execute(query, (project_name,))
            results = self.cursor.fetchall()

            citation_list = []
            for row in results:
                citation = CitationData(*row)
                citation_list.append(citation)

            return citation_list
        except Exception as err:
            msg = "Error retrieving citations for directory"
            logger.exception(msg)
            raise Exception(msg)

    def get_numberofdirectories_in_project(self, name: str) -> int:
        try:
            query = f"""
                SELECT count(distinct unique_name)
                FROM {self.DIRECTORY_TABLE}
                WHERE parent_project = %s
            """
            self.cursor.execute(query, (name, ))  
            result = self.cursor.fetchone()

            if result:
                return result[0]
            else:
                return 0
        except Exception as err:
            msg = f"Error retrieving directory count for {name} from the database"
            logger.exception(msg)
            raise Exception(msg)

    def get_numberoffiles_under_directory(self, unique_name: str) -> int:
        try:
            query = f"""
                SELECT count(distinct file_name)
                FROM {self.FILE_TABLE}
                WHERE parent_directory = %s OR parent_directory LIKE %s
            """
            self.cursor.execute(query, (unique_name, unique_name + '::%', ))  # Attach % for string matching 
            result = self.cursor.fetchone()

            if result:
                return result[0]
            else:
                return 0
        except Exception as err:
            msg = f"Error retrieving file count for {unique_name} from the database"
            logger.exception(msg)
            raise Exception(msg)
    
    def get_numberoffiles_within_directory(self, unique_name: str) -> int:
        try:
            query = f"""
                SELECT count(distinct file_name)
                FROM {self.FILE_TABLE}
                WHERE parent_directory = %s
            """
            self.cursor.execute(query, (unique_name, )) 
            result = self.cursor.fetchone()
    
            if result:
                return result[0]
            else:
                return 0
        except Exception as err:
            msg = f"Error retrieving file count for {unique_name} from the database"
            logger.exception(msg)
            raise Exception(msg)

    def get_favorites_by_user(self, username: str) -> List['DirectoryData']:
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.FAVORITE_TABLE} f JOIN {self.DIRECTORY_TABLE} d ON f.directory=d.unique_name
                WHERE f.username = %s
            """
            self.cursor.execute(query, (username,))
            results = self.cursor.fetchall()

            directory_list = []
            for row in results:
                directory = DirectoryData(*row)
                directory_list.append(directory)

            return directory_list
        except Exception as err:
            msg = f"Error retrieving favorite directories for this user {username}"
            logger.exception(msg)
            raise Exception(msg)
        
    def is_favorited_by_user(self, directory:str, username: str) -> bool:
        try:
            query = f"""
                SELECT count(*)
                FROM {self.FAVORITE_TABLE}
                WHERE username = %s and directory=%s
            """
            self.cursor.execute(query, (username, directory))
            result = self.cursor.fetchall()

            if result:
                if result[0][0] >= 1:
                    return True
                else:
                    return False
            else:
                return False

        except Exception as err:
            print(err)
            msg = f"Error retrieving favorite directories for this user {username}"
            logger.exception(msg)
            raise Exception(msg)
    

    # --------- Update Tables -------- #
    def update_attribute(self, table_name: str, attribute_name: str, new_value: str, condition_column: str = None, condition_value: str = None, second_condition_column: str = None, second_condition_value: str = None) -> None:
        try:
            if second_condition_column and second_condition_value:
                query = f"""
                    UPDATE {table_name}
                    SET {attribute_name} = %s
                    WHERE {condition_column} = %s AND {second_condition_column} = %s
                """
                self.cursor.execute(
                    query, (new_value, condition_value, second_condition_value))
            elif condition_column and condition_value:
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
            msg = f"Error updating {attribute_name} in {table_name}"
            logger.exception(msg)
            raise Exception(msg)

    # -------- Delete From Tables ------- #

    def delete_project_by_name(self, project_name: str) -> None:
        try:
            query = f"""
                DELETE FROM {self.PROJECT_TABLE} WHERE name = %s
            """
            self.cursor.execute(query, (project_name,))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting project by name"
            logger.exception(msg)
            raise Exception(msg)

    def delete_directory_by_name(self, unique_name: str) -> None:
        try:
            query = f"""
                DELETE FROM {self.DIRECTORY_TABLE} WHERE unique_name = %s
            """
            self.cursor.execute(query, (unique_name,))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting directory by unique name"
            logger.exception(msg)
            raise Exception(msg)

    def delete_file_by_name(self, file_name: str) -> None:
        try:
            query = f"""
                DELETE FROM {self.FILE_TABLE} WHERE file_name = %s
            """
            self.cursor.execute(query, (file_name,))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting file by name"
            logger.exception(msg)
            raise Exception(msg)

    def delete_citation(self, cit_id: int) -> None:
        try:
            query = """
                DELETE FROM Citation WHERE cit_id = %s
            """
            self.cursor.execute(query, (cit_id, ))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting citation by id."
            logger.exception(msg)
            raise Exception(msg)
    
    def delete_favorite(self, directory:str, username:str) -> None:
        try:
            query = f"""
                DELETE FROM {self.FAVORITE_TABLE} WHERE directory = %s AND username = %s
            """
            self.cursor.execute(query, (directory, username))
            self.conn.commit()
        except Exception as err:
            msg = f"Error removing {directory} as a favorite for {username}."
            logger.exception(msg)
            raise Exception(msg)

    # -------- Helpers ------- #

    def get_next_available_filename(self, original_filename):
        # Extract the base name without extension
        base_name, extension = os.path.splitext(original_filename)
        # Initialize a counter
        counter = 1
        while True:
            # Construct the new file name
            new_filename = f"{base_name}({counter}){extension}"
            # Check if this filename exists in the database
            if not self.filename_exists(new_filename):
                return new_filename
            counter += 1

    def filename_exists(self, filename):
        # Check if the given filename already exists in the database
        self.cursor.execute(f"SELECT COUNT(*) FROM {self.FILE_TABLE} WHERE file_name = %s", (filename,))
        count = self.cursor.fetchone()[0]
        return count > 0

    def get_next_available_file_data(self, original_data):
        # Create a new instance of FileData with an updated file_name
        new_file_name = self.get_next_available_filename(original_data.file_name)
        return FileData(
            file_name=new_file_name,
            parent_directory=original_data.parent_directory,
            format=original_data.format,
            tags=original_data.tags,
            modality=original_data.modality,
            timestamp_creation=original_data.timestamp_creation,
            timestamp_last_updated=original_data.timestamp_last_updated
        )


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
    project_name: str


class FileData(NamedTuple):
    file_name: str
    parent_directory: str
    format: str
    size: float
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
