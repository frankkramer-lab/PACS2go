from datetime import datetime, timedelta
import os
from typing import List, NamedTuple

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from pytz import timezone

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, FailedDisconnectException)
from pacs2go.data_interface.logs.config_logging import logger

INSIDE_DOCKER = True  # Change this to False if run outside the Docker container

if INSIDE_DOCKER:
    DATABASE_HOST = 'data-structure-db'
    DATABASE_PORT = 5432
else:
    DATABASE_HOST = 'localhost'
    DATABASE_PORT = 5433

load_dotenv()

class PACS_DB():
    """
    Class to interact with the PACS database.

    Attributes:
        PROJECT_TABLE (str): Name of the project table.
        DIRECTORY_TABLE (str): Name of the directory table.
        CITATION_TABLE (str): Name of the citation table.
        FILE_TABLE (str): Name of the file table.
        FAVORITE_TABLE (str): Name of the favorite directories table.
        PROJECT_ACCESS_REQUEST_TABLE (str): Name of the project access request table.
        USER_ACTIVITY_TABLE (str): Name of the user activity table.
    """
    
    PROJECT_TABLE = "Project"
    DIRECTORY_TABLE = "Directory"
    CITATION_TABLE = "Citation"
    FILE_TABLE = "File"
    FAVORITE_TABLE = "FavoriteDirectories"
    PROJECT_ACCESS_REQUEST_TABLE = "RequestProjectAccess"
    USER_ACTIVITY_TABLE = "UserActivity"

    def __init__(self, host: str = "data-structure-db", port: int = 5432) -> None:
        """
        Initialize the database connection.

        Args:
            host (str): Host address of the database.
            port (int): Port number of the database.

        Raises:
            FailedConnectionException: If connection to the database fails.
        """
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
        """
        Close the database connection.

        Raises:
            FailedDisconnectException: If disconnection from the database fails.
        """
        try:
            self.cursor.close()
            self.conn.close()
        except:
            msg = "DB server disconnect was not successful."
            logger.exception(msg)
            raise FailedDisconnectException(msg)

    # -------- Create Tables ------- #

    def create_tables(self):
        """Create all necessary tables in the database."""
        self.create_table_project()
        self.create_table_directory()
        self.create_table_citation()
        self.create_table_file()
        self.create_table_favorite_directories()
        self.create_table_project_access_request()
        self.create_table_user_activity()

    def create_table_project(self):
        """Create the Project table."""
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
        """Create the Directory table."""
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
        """Create the Citation table."""
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
        """Create the File table."""
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
        """Create the FavoriteDirectories table."""
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
        
    def create_table_project_access_request(self):
        """Create the ProjectAccessRequest table."""
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.PROJECT_ACCESS_REQUEST_TABLE} (
                    req_id SERIAL PRIMARY KEY,
                    project VARCHAR(256) REFERENCES {self.PROJECT_TABLE}(name) ON DELETE CASCADE,
                    username VARCHAR(128)
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"{self.PROJECT_ACCESS_REQUEST_TABLE} table could not be created."
            logger.exception(msg)
            raise Exception(msg)
        
    def create_table_user_activity(self):
        """Create the UserActivity table."""
        try:
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.USER_ACTIVITY_TABLE} (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(128) NOT NULL,
                    directory VARCHAR(256) REFERENCES {self.DIRECTORY_TABLE}(unique_name) ON DELETE CASCADE,
                    last_checked_timestamp TIMESTAMP NOT NULL,
                    UNIQUE(username, directory)
                )
            """)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"{self.USER_ACTIVITY_TABLE} table could not be created."
            logger.exception(msg)
            raise Exception(msg)
            
    # -------- Insert Into Tables ------- #

    def insert_into_project(self, data: 'ProjectData') -> None:
        """
        Insert a project into the Project table.

        Args:
            data (ProjectData): The data to insert.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
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
        """
        Insert a directory into the Directory table.

        Args:
            data (DirectoryData): The data to insert.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.DIRECTORY_TABLE} (unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (data.unique_name, data.dir_name, data.parent_project, data.parent_directory, data.timestamp_creation, data.parameters, data.timestamp_last_updated))
            self.conn.commit()
        except psycopg2.IntegrityError as e: ## TODO: take care of duplicate directory names in a more user-friendly manner (similarly to files perhabs)
            self.conn.rollback()
            msg = f"Error inserting {data.dir_name} into Directory table due to duplicate directory name. Make sure to rename your top-level directory before uploading."
            logger.exception(msg)
            raise Exception(msg)
        except Exception as err:
            self.conn.rollback()
            msg = f"Error inserting {data.dir_name} into Directory table"
            logger.exception(msg)
            raise Exception(msg)

    def insert_into_citation(self, data: 'CitationData') -> None:
        """
        Insert a citation into the Citation table.

        Args:
            data (CitationData): The data to insert.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
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
        """
        Insert a file into the File table.

        Args:
            data (FileData): The data to insert.

        Returns:
            FileData: The inserted file data.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
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
        """
        Insert multiple files into the File table.

        Args:
            files (List[FileData]): List of files to insert.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
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
        """
        Insert a favorite directory for a user.

        Args:
            directory (str): Directory name.
            username (str): Username.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
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
        
    def insert_request_to_project(self, project, username) -> None:
        """
        Insert a project access request for a user.

        Args:
            project (str): Project name.
            username (str): Username.

        Raises:
            Exception: If an error occurs while inserting the data.
        """
        try:
            self.cursor.execute(f"""
                INSERT INTO {self.PROJECT_ACCESS_REQUEST_TABLE} (project, username)
                VALUES (%s, %s)
            """, (project, username))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            msg = f"Error inserting into {self.PROJECT_ACCESS_REQUEST_TABLE} table"
            logger.exception(msg)
            raise Exception(msg)
        

    # -------- Select From Tables ------- #

    def get_all_projects(self) -> List['ProjectData']:
        """
        Retrieve all projects from the Project table.

        Returns:
            List[ProjectData]: List of all projects.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            query = f"""
                SELECT name, keywords, description, parameters, timestamp_creation, timestamp_last_updated
                FROM {self.PROJECT_TABLE}
                ORDER BY timestamp_last_updated DESC
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
        """
        Retrieve all directories from the Directory table.

        Returns:
            List[DirectoryData]: List of all directories.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
                ORDER BY timestamp_last_updated DESC
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
        """
        Retrieve all files from a specific directory.

        Args:
            directory_name (str): Directory name.

        Returns:
            List[str]: List of all file names in the directory.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Retrieve a slice of files from a directory with optional filter, quantity, and offset.

        Args:
            directory_name (str): Directory name.
            filter (str, optional): Filter string for file names or tags.
            quantity (int, optional): Number of files to retrieve.
            offset (int, optional): Number of rows to skip before retrieving files.

        Returns:
            List[FileData]: List of files matching the criteria.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Retrieve a project by its name.

        Args:
            project_name (str): Project name.

        Returns:
            ProjectData: The project data.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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

    def get_directories_by_project(self, project_name: str, filter: str = None, offset: int = None, quantity: int = None) -> List['DirectoryData']:  
        """
        Retrieve directories belonging to a specific project with optional filter, offset, and quantity.

        Args:
            project_name (str): Project name.
            filter (str, optional): Filter string for directory names.
            offset (int, optional): Number of rows to skip before retrieving directories.
            quantity (int, optional): Number of directories to retrieve.

        Returns:
            List[DirectoryData]: List of directories matching the criteria.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            # Start with the base query
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
                WHERE parent_project = %s
            """

            # Prepare the list for parameters of the SQL query
            params = [project_name]

            # If a filter is provided, add the LIKE clause
            if filter:
                query += " AND dir_name LIKE %s"
                params.append(f"%{filter}%")

            # Add ordering (necessary for limit offset in particular)
            query += " ORDER BY dir_name"

            # If both offset and quantity are provided, add LIMIT and OFFSET to the query
            if offset is not None and quantity is not None:
                query += " LIMIT %s OFFSET %s"
                params.extend([quantity, offset])

            # Execute the query
            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()

            # Build the directory list from the results
            directory_list = [DirectoryData(*row) for row in results]

            return directory_list
        except Exception as err:
            msg = "Error retrieving directories by project"
            logger.exception(msg)
            raise Exception(msg)
        
    def get_all_directories_including_subdirectories_by_project(self, project_name: str) -> List['DirectoryData']:  
        """
        Retrieve all directories, including subdirectories, belonging to a specific project.

        Args:
            project_name (str): Project name.

        Returns:
            List[DirectoryData]: List of directories.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            # Start with the base query
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
                WHERE unique_name LIKE %s
            """

            # Execute the query
            self.cursor.execute(query, (f"{project_name}%",))
            results = self.cursor.fetchall()

            # Build the directory list from the results
            directory_list = [DirectoryData(*row) for row in results]

            return directory_list
        except Exception as err:
            msg = "Error retrieving directories by project"
            logger.exception(msg)
            raise Exception(msg)

    def get_directory_by_name(self, unique_name: str) -> 'DirectoryData':
        """
        Retrieve a directory by its unique name.

        Args:
            unique_name (str): Directory unique name.

        Returns:
            DirectoryData: The directory data.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Retrieve a file by its name and parent directory.

        Args:
            file_name (str): File name.
            parent_directory (str): Parent directory name.

        Returns:
            FileData: The file data.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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

    def get_subdirectories_by_directory(self, parent_directory: str, filter: str = None, offset: int = None, quantity: int = None) -> List['DirectoryData']:
        """
        Retrieve subdirectories belonging to a specific directory with optional filter, offset, and quantity.

        Args:
            parent_directory (str): Parent directory name.
            filter (str, optional): Filter string for subdirectory names.
            offset (int, optional): Number of rows to skip before retrieving subdirectories.
            quantity (int, optional): Number of subdirectories to retrieve.

        Returns:
            List[DirectoryData]: List of subdirectories matching the criteria.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            # Start with the base query
            query = f"""
                SELECT unique_name, dir_name, parent_project, parent_directory, timestamp_creation, parameters, timestamp_last_updated
                FROM {self.DIRECTORY_TABLE}
                WHERE parent_directory = %s
            """

            # Prepare the list for parameters of the SQL query
            params = [parent_directory]

            # If a filter is provided, add the LIKE clause
            if filter:
                query += " AND dir_name LIKE %s"
                params.append(f"%{filter}%")

            # Add ordering (necessary for limit offset in particular)
            query += " ORDER BY dir_name"

            # If both offset and quantity are provided, add LIMIT and OFFSET to the query
            if offset is not None and quantity is not None:
                query += " LIMIT %s OFFSET %s"
                params.extend([quantity, offset])

            # Execute the query
            self.cursor.execute(query, tuple(params))
            results = self.cursor.fetchall()

            # Build the directory list from the results
            directory_list = [DirectoryData(*row) for row in results]

            return directory_list
        except Exception as err:
            msg = "Error retrieving subdirectories by directory"
            logger.exception(msg)
            raise Exception(msg)

    def get_citations_for_project(self, project_name: str) -> List['CitationData']:
        """
        Retrieve citations for a specific project.

        Args:
            project_name (str): Project name.

        Returns:
            List[CitationData]: List of citations.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Retrieve the number of directories in a specific project.

        Args:
            name (str): Project name.

        Returns:
            int: Number of directories.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        
    def get_numberofsubdirectories_under_directory(self, unique_name: str) -> int:
        """
        Retrieve the number of subdirectories under a specific directory.

        Args:
            unique_name (str): Directory unique name.

        Returns:
            int: Number of subdirectories.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            query = f"""
                SELECT count(*)
                FROM {self.DIRECTORY_TABLE}
                WHERE parent_directory = %s
            """
            self.cursor.execute(query, (unique_name, ))  # Attach % for string matching 
            result = self.cursor.fetchone()

            if result:
                return result[0]
            else:
                return 0
        except Exception as err:
            msg = f"Error retrieving subdirectory count for {unique_name} from the database"
            logger.exception(msg)
            raise Exception(msg)

    def get_numberoffiles_under_directory(self, unique_name: str) -> int:
        """
        Retrieve the number of files under a specific directory.

        Args:
            unique_name (str): Directory unique name.

        Returns:
            int: Number of files.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            query = f"""
                SELECT count(*)
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
        """
        Retrieve the number of files within a specific directory.

        Args:
            unique_name (str): Directory unique name.

        Returns:
            int: Number of files.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Retrieve favorite directories for a specific user.

        Args:
            username (str): Username.

        Returns:
            List[DirectoryData]: List of favorite directories.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        """
        Check if a directory is favorited by a specific user.

        Args:
            directory (str): Directory name.
            username (str): Username.

        Returns:
            bool: True if favorited, False otherwise.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
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
        
    def get_requests_to_project(self, project: str) -> list:
        """
        Retrieve project access requests for a specific project.

        Args:
            project (str): Project name.

        Returns:
            list: List of usernames requesting access.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            query = f"""
                SELECT username
                FROM {self.PROJECT_ACCESS_REQUEST_TABLE}
                WHERE project = %s
            """
            self.cursor.execute(query, (project,))
            results = self.cursor.fetchall()
     
            user_list = []
            for row in results:
                user_list.append(*row)

            return user_list
        except Exception as err:
            msg = f"Error retrieving requests to Project {project}"
            logger.exception(msg)
            raise Exception(msg)
        
    def get_new_files_for_user(self, username: str, directory: str) -> List[str]:
        """
        Retrieve new files for a specific user in a directory.

        Args:
            username (str): Username.
            directory (str): Directory name.

        Returns:
            List[str]: List of new file names.

        Raises:
            Exception: If an error occurs while retrieving the data.
        """
        try:
            # First, retrieve the last_checked_timestamp for the user and directory
            self.cursor.execute(f"""
                SELECT last_checked_timestamp
                FROM {self.USER_ACTIVITY_TABLE}
                WHERE username = %s AND directory = %s
            """, (username, directory))
            result = self.cursor.fetchone()
            last_checked = result[0] if result else (datetime.min + timedelta(minutes=10))

            # Next, retrieve files that are new or updated since last_checked (minus 10 minutes to visualize new files for 10 minutes)
            self.cursor.execute(f"""
                SELECT file_name
                FROM {self.FILE_TABLE}
                WHERE parent_directory = %s AND 
                (timestamp_creation > (%s - interval '10 minute') OR timestamp_last_updated > (%s - interval '10 minute'))
            """, (directory, last_checked, last_checked))
            files = self.cursor.fetchall()

            return [file[0] for file in files] if files else []
        except Exception as err:
            msg = f"Error retrieving new files for {directory} and {username}" + str(err)
            logger.exception(msg)
            raise Exception(msg)      

    # --------- Update Tables -------- #
    def update_attribute(self, table_name: str, attribute_name: str, new_value: str, condition_column: str = None, condition_value: str = None, second_condition_column: str = None, second_condition_value: str = None) -> None:
        """
        Update an attribute in a table.

        Args:
            table_name (str): Table name.
            attribute_name (str): Attribute name to update.
            new_value (str): New value for the attribute.
            condition_column (str, optional): Column to apply condition.
            condition_value (str, optional): Value for the condition column.
            second_condition_column (str, optional): Second column to apply condition.
            second_condition_value (str, optional): Value for the second condition column.

        Raises:
            Exception: If an error occurs while updating the data.
        """
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

    def update_multiple_files(self, file_names:list, modality:str, tags:str, directory_name:str) -> None:
        """
        Update multiple files' modality and tags.

        Args:
            file_names (list): List of file names.
            modality (str): New modality value.
            tags (str): New tags value.
            directory_name (str): Directory name.

        Raises:
            Exception: If an error occurs while updating the data.
        """
        try:
            time = datetime.now(timezone("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")
            placeholders = ', '.join(['%s'] * len(file_names))

            query = f"""
                UPDATE {self.FILE_TABLE} SET modality=%s, tags=%s, timestamp_last_updated=%s WHERE parent_directory=%s AND file_name IN ({placeholders})
            """
            self.cursor.execute(query, (modality, tags, time, directory_name) + tuple(file_names))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting file by name"
            logger.exception(msg)
            raise Exception(msg)
    
    def update_user_activity(self, username: str, directory: str):
        """
        Update user activity timestamp for a directory.

        Args:
            username (str): Username.
            directory (str): Directory name.

        Raises:
            Exception: If an error occurs while updating the data.
        """
        current_time = datetime.now(timezone("Europe/Berlin")).strftime("%Y-%m-%d %H:%M:%S")

        try:
            self.cursor.execute(f"""
                INSERT INTO {self.USER_ACTIVITY_TABLE} (username, directory, last_checked_timestamp)
                VALUES (%s, %s, %s)
                ON CONFLICT (username, directory)
                DO UPDATE SET last_checked_timestamp = EXCLUDED.last_checked_timestamp
            """, (username, directory, current_time))
            self.conn.commit()
        except Exception as err:
            print(err)
            self.conn.rollback()
            logger.exception("Error updating user activity in DB.")
            raise


    # -------- Delete From Tables ------- #

    def delete_project_by_name(self, project_name: str) -> None:
        """
        Delete a project by its name.

        Args:
            project_name (str): Project name.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
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
        """
        Delete a directory by its unique name.

        Args:
            unique_name (str): Directory unique name.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
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

    def delete_file_by_name(self, file_name: str, directory_name:str) -> None:
        """
        Delete a file by its name and parent directory.

        Args:
            file_name (str): File name.
            directory_name (str): Parent directory name.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
        try:
            query = f"""
                DELETE FROM {self.FILE_TABLE} WHERE file_name = %s and parent_directory=%s
            """
            self.cursor.execute(query, (file_name, directory_name))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting file by name"
            logger.exception(msg)
            raise Exception(msg)
        
    def delete_multiple_files_by_name(self, file_names: list, directory_name:str) -> None:
        """
        Delete multiple files by their names and parent directory.

        Args:
            file_names (list): List of file names.
            directory_name (str): Parent directory name.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
        try:
            placeholders = ', '.join(['%s'] * len(file_names))
            query = f"""
                DELETE FROM {self.FILE_TABLE} WHERE parent_directory=%s AND file_name IN ({placeholders})
            """
            self.cursor.execute(query, (directory_name,) + tuple(file_names))
            self.conn.commit()
        except Exception as err:
            msg = "Error deleting file by name"
            logger.exception(msg)
            raise Exception(msg)

    def delete_citation(self, cit_id: int) -> None:
        """
        Delete a citation by its ID.

        Args:
            cit_id (int): Citation ID.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
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
        """
        Delete a favorite directory for a user.

        Args:
            directory (str): Directory name.
            username (str): Username.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
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
        
    def delete_request(self, project:str, username:str) -> None:
        """
        Delete a project access request for a user.

        Args:
            project (str): Project name.
            username (str): Username.

        Raises:
            Exception: If an error occurs while deleting the data.
        """
        try:
            query = f"""
                DELETE FROM {self.PROJECT_ACCESS_REQUEST_TABLE} WHERE project = %s AND username = %s
            """
            self.cursor.execute(query, (project, username))
            self.conn.commit()
        except Exception as err:
            msg = f"Error removing {username} 's request for Project {project}."
            logger.exception(msg)
            raise Exception(msg)


    # -------- Helpers ------- #

    def get_next_available_filename(self, original_filename, directory_name):
        """
        Get the next available filename in a directory to avoid duplicates.

        Args:
            original_filename (str): Original file name.
            directory_name (str): Directory name.

        Returns:
            str: Next available file name.
        """
        # Extract the base name without extension
        base_name, extension = os.path.splitext(original_filename)
        # Initialize a counter
        counter = 1
        while True:
            # Construct the new file name
            new_filename = f"{base_name}({counter}){extension}"
            # Check if this filename exists in the database
            if not self.filename_exists(new_filename, directory_name):
                return new_filename
            counter += 1

    def filename_exists(self, filename, directory_name):
        """
        Check if a filename already exists in a directory.

        Args:
            filename (str): File name.
            directory_name (str): Directory name.

        Returns:
            bool: True if the filename exists, False otherwise.
        """
        # Check if the given filename already exists in the database
        self.cursor.execute(f"SELECT COUNT(*) FROM {self.FILE_TABLE} WHERE file_name = %s AND parent_directory= %s", (filename, directory_name))
        count = self.cursor.fetchone()[0]
        return count > 0

    def get_next_available_file_data(self, original_data):
        """
        Get the next available file data to avoid duplicate file names.

        Args:
            original_data (FileData): Original file data.

        Returns:
            FileData: New file data with an updated file name.
        """

        # Create a new instance of FileData with an updated file_name
        new_file_name = self.get_next_available_filename(original_data.file_name, original_data.parent_directory)
        return FileData(
            file_name=new_file_name,
            parent_directory=original_data.parent_directory,
            format=original_data.format,
            size=original_data.size,
            tags=original_data.tags,
            modality=original_data.modality,
            timestamp_creation=original_data.timestamp_creation,
            timestamp_last_updated=original_data.timestamp_last_updated
        )


# Named Tuples
class ProjectData(NamedTuple):
    """
    Named tuple for project data.

    Attributes:
        name (str): Project name.
        keywords (str): Project keywords.
        description (str): Project description.
        parameters (str): Project parameters.
        timestamp_creation (str): Project creation timestamp.
        timestamp_last_updated (str): Project last updated timestamp.
    """
    name: str
    keywords: str
    description: str
    parameters: str
    timestamp_creation: str
    timestamp_last_updated: str


class DirectoryData(NamedTuple):
    """
    Named tuple for directory data.

    Attributes:
        unique_name (str): Directory unique name.
        dir_name (str): Directory name.
        parent_project (str): Parent project name.
        parent_directory (str): Parent directory name if subdirectory.
        timestamp_creation (str): Directory creation timestamp.
        parameters (str): Directory parameters.
        timestamp_last_updated (str): Directory last updated timestamp.
    """
    unique_name: str
    dir_name: str
    parent_project: str
    parent_directory: str
    timestamp_creation: str
    parameters: str
    timestamp_last_updated: str


class CitationData(NamedTuple):
    """
    Named tuple for citation data.

    Attributes:
        cit_id (int): System generated Citation ID.
        citation (str): Citation text in a common citation style (e.g.: Vancouver).
        link (str): Citation link, e.g.: kaggle.com/xyzabc or DOI.
        project_name (str): Project name.
    """
    cit_id: int
    citation: str
    link: str
    project_name: str


class FileData(NamedTuple):
    """
    Named tuple for file data.

    Attributes:
        file_name (str): File name.
        parent_directory (str): Parent directory name.
        format (str): File format.
        size (float): File size.
        tags (str): File tags.
        modality (str): File modality. (CT, MRI etc)
        timestamp_creation (str): File creation/upload timestamp.
        timestamp_last_updated (str): File last updated timestamp.
    """
    file_name: str
    parent_directory: str
    format: str
    size: float
    tags: str
    modality: str
    timestamp_creation: str
    timestamp_last_updated: str


# Test the PACS_DB class
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
