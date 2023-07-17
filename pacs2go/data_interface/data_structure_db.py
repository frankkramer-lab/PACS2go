from typing import NamedTuple
from typing import Union

import psycopg2


class Metadata_DB():
    def __init__(self,host:str= "localhost") -> None:
        # Connect to the Postgres service
        self.conn = psycopg2.connect(
            host="data-structure-db",
            port=5432,
            user="myuser",
            password="mypassword",
            database="mydb"
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
            print("Directory table could not be created. " + str(err))
            
    def create_table_file(self):
        try:
            # Create a table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS File (
                    file_name VARCHAR(60) NOT NULL,
                    parent_directory VARCHAR(60) REFERENCES Directory(unique_name) ON DELETE CASCADE,
                    PRIMARY KEY(file_name)
                )
            """)
            # Commit the changes
            self.conn.commit()
        except Exception as err:
            print("File table could not be created. " + str(err))


    # -------- Insert Into Tables ------- #

    def insert_into_project(self, data: 'ProjectData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Project (name) VALUES (%s)
            """, (data.name,))
            self.conn.commit()
        except Exception as err:
            print("Error inserting into Project table: " + str(err))

    def insert_into_directory(self, data: 'DirectoryData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO Directory (unique_name, dir_name, parent_project, parent_directory)
                VALUES (%s, %s, %s, %s)
            """, (data.unique_name, data.dir_name, data.parent_project, data.parent_directory))
            self.conn.commit()
        except Exception as err:
            print("Error inserting into Directory table: " + str(err))

    def insert_into_file(self, data: 'FileData') -> None:
        try:
            self.cursor.execute("""
                INSERT INTO File (file_name, parent_directory) VALUES (%s, %s)
            """, (data.file_name, data.parent_directory))
            self.conn.commit()
        except Exception as err:
            print("Error inserting into File table: " + str(err))


    # -------- Select From Tables ------- #

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
