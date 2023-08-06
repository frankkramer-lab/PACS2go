from typing import NamedTuple, List

import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

class PACS_DB():
    def __init__(self) -> None:
        # Connect to the Postgres service
        self.conn = psycopg2.connect(
            host="data-structure-db",
            port=5432,
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB")
        )
        # Get cursor object to operate db
        self.cursor = self.conn.cursor()

        # On inital setup create tables (all statements possess IF NOT EXISTS keyword)
        self.create_tables()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.cursor.close()
        self.conn.close()

    # -------- Create Tables ------- #

    def create_tables(self):
        self.create_table_project()
        self.create_table_directory()
        self.create_table_file()

    def create_table_project(self):
        try:
            # Create a table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Project (
                    name VARCHAR(60) NOT NULL,
                    PRIMARY KEY(name)
                )
            """)
            # Commit the changes
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Project table could not be created. " + str(err))

    def create_table_directory(self):
        try:
            # Create a table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS Directory (
                    unique_name VARCHAR(60) NOT NULL,
                    dir_name VARCHAR(60) NOT NULL,
                    parent_project VARCHAR(60) REFERENCES Project(name) ON DELETE CASCADE,
                    parent_directory VARCHAR(60) REFERENCES Directory(unique_name) ON DELETE CASCADE,
                    PRIMARY KEY(unique_name)
                )
            """)
            # Commit the changes
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Directory table could not be created. " + str(err))
            
    def create_table_file(self):
        try:
            # Create a table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS File (
                    file_name VARCHAR(60) NOT NULL,
                    parent_directory VARCHAR(60) NOT NULL,
                    PRIMARY KEY(file_name, parent_directory),
                    FOREIGN KEY (parent_directory) REFERENCES Directory(unique_name) ON DELETE CASCADE
                )
            """)
            # Commit the changes
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("File table could not be created. " + str(err))


    # -------- Insert Into Tables ------- #

    def insert_into_project(self, data: 'ProjectData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Project (name) VALUES (%s)
            """, (data.name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Error inserting into Project table: " + str(err))

    def insert_into_directory(self, data: 'DirectoryData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Directory (unique_name, dir_name, parent_project, parent_directory)
                VALUES (%s, %s, %s, %s)
            """, (data.unique_name, data.dir_name, data.parent_project, data.parent_directory))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Error inserting into Directory table: " + str(err))

    def insert_into_file(self, data: 'FileData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO File (file_name, parent_directory) VALUES (%s, %s)
            """, (data.file_name, data.parent_directory))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Error inserting into File table: " + str(err))
    
        
    def insert_multiple_files(self, files: List['FileData']) -> None:
        try:
            # Construct a list of tuples with (file_name, parent_directory) for each file
            file_values = [(file.file_name, file.parent_directory) for file in files]

            query = """
                INSERT INTO File (file_name, parent_directory)
                VALUES %s
                ON CONFLICT (file_name) DO NOTHING
            """
            execute_values(self.cursor, query, file_values)
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print(f"Error inserting multiple files: {err}")


    # -------- Select From Tables ------- #

    def get_all_projects(self) -> list:
        try:
            query = """
                SELECT name FROM Project
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()

            project_list = []
            for row in results:
                project_name = row[0]
                project_list.append(project_name)

            return project_list
        except Exception as err:
            print("Error retrieving all projects: " + str(err))
            return []
        
    def get_all_directories(self) -> list:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory
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
            print("Error retrieving all directories: " + str(err))
            return []


    def get_all_files(self) -> list:
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
            print("Error retrieving all projects: " + str(err))
            return []

    def get_directories_by_project(self, project_name: str) -> list:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory
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
            print("Error retrieving directories by project: " + str(err))
            return []

    def get_directory_by_name(self, unique_name: str) -> 'DirectoryData':
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory
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
            print("Error retrieving directory from the database: " + str(err))
            return None

    def get_subdirectories_by_directory(self, parent_directory: str) -> list:
        try:
            query = """
                SELECT unique_name, dir_name, parent_project, parent_directory
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
            print("Error retrieving directories by directory: " + str(err))
            return []
        

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
            print("Error deleting project by name: " + str(err))

    def delete_directory_by_name(self, unique_name: str) -> None:
        try:
            query = """
                DELETE FROM Directory WHERE unique_name = %s
            """
            self.cursor.execute(query, (unique_name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Error deleting directory by unique name: " + str(err))

    def delete_file_by_name(self, file_name: str) -> None:
        try:
            query = """
                DELETE FROM File WHERE file_name = %s
            """
            self.cursor.execute(query, (file_name,))
            self.conn.commit()
        except Exception as err:
            self.conn.rollback()
            print("Error deleting file by name: " + str(err))


# Named Tuples
class ProjectData(NamedTuple):
    name: str


class DirectoryData(NamedTuple):
    unique_name: str
    dir_name: str
    parent_project: str
    parent_directory: str


class FileData(NamedTuple):
    file_name: str
    parent_directory: str


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