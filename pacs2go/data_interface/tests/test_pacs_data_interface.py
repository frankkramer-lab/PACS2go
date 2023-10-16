import os
import unittest
import uuid

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulGetException, WrongUploadFormatException)
from pacs2go.data_interface.pacs_data_interface import (Connection)


class TestConnection(unittest.TestCase):
    def test_successful_connection(self):
        connection = Connection('http://localhost:8888', 'test_user', 'test', kind='XNAT')
        self.assertIsNotNone(connection.user)

    def test_invalid_connection(self):
        with self.assertRaises(FailedConnectionException):
            connection = Connection('invalid-server', 'test_user', 'test', kind='XNAT')

class TestProject(unittest.TestCase):
    def run(self, result=None):
        with Connection('http://localhost:8888', 'test_user', 'test', kind='XNAT', db_host='localhost', db_port=5433) as connection:
            self.connection = connection
            self.session = connection.session_id
            super(TestProject, self).run(result)

    @classmethod
    def setUpClass(self):
        with Connection('http://localhost:8888', 'test_user', 'test', kind='XNAT', db_host='localhost', db_port=5433) as connection:
            self.project = connection.create_project(str(uuid.uuid4()))

    @classmethod
    def tearDownClass(self):
        if self.project.exists():
            self.project.delete_project()

    def test_project_description(self):
        self.project.set_description('New description')
        self.assertEqual(self.project.description, 'New description')

    def test_project_keywords(self):
        self.assertEqual(self.project.keywords, 'Set keywords here.')
        self.project.set_keywords('keyword1,keyword2')
        self.assertEqual(self.project.keywords, 'keyword1,keyword2')

    def test_create_and_get_directory(self):
        directory = self.project.create_directory(str(uuid.uuid4()))
        self.assertIsNotNone(directory)

        retrieved_directory = self.project.get_directory(directory.name)
        self.assertIsNotNone(retrieved_directory)

        self.assertEqual(directory.name, retrieved_directory.name)
        self.assertEqual(directory.display_name, retrieved_directory.display_name)

    def test_get_all_directories(self):
        directories = self.project.get_all_directories()
        self.assertIsInstance(directories, list)

    def test_insert_file(self):
        with open('test.txt', 'w') as f:
            f.write('Test content')

        file = self.project.insert('test.txt')
        self.assertTrue(file.exists())
        os.remove('test.txt')


    def test_insert_invalid_file(self):
        with self.assertRaises(WrongUploadFormatException):
            self.project.insert('invalid_file.txt', 'test_directory')

class TestDirectory(unittest.TestCase):
    def setUp(self):
        self.connection = Connection('http://localhost:8888', 'test_user', 'test', kind='XNAT', db_host='localhost', db_port=5433)
        self.project = self.connection.create_project(str(uuid.uuid4()))
        self.directory = self.project.create_directory(str(uuid.uuid4()))

    def tearDown(self):
        self.project.delete_project()

    def test_create_and_get_subdirectory(self):
        subdirectory = self.directory.create_subdirectory(str(uuid.uuid4()))
        self.assertIsNotNone(subdirectory)

        self.assertGreater(len(self.directory.get_subdirectories()),0)
        retrieved_subdirectory = self.directory.get_subdirectories()[0]
        self.assertIsNotNone(retrieved_subdirectory)

        self.assertEqual(subdirectory.name, retrieved_subdirectory.name)
        self.assertEqual(subdirectory.display_name, retrieved_subdirectory.display_name)

    def test_get_all_files(self):
        files = self.directory.get_all_files()
        self.assertIsInstance(files, list)

class TestFile(unittest.TestCase):
    def setUp(self):
        self.connection = Connection('http://localhost:8888', 'test_user', 'test', kind='XNAT', db_host='localhost', db_port=5433)
        self.project = self.connection.create_project(str(uuid.uuid4()))
        self.directory = self.project.create_directory(str(uuid.uuid4()))
        self.file_path = 'test_file.txt'
        with open(self.file_path, 'w') as f:
            f.write('Test content')

    def tearDown(self):
        os.remove(self.file_path)
        self.project.delete_project()

    def test_delete_file(self):
        file = self.project.insert(self.file_path, self.directory.name)
        self.assertIsNotNone(file)

        file.delete_file()
        with self.assertRaises(UnsuccessfulGetException):
            self.directory.get_file(file.name)

if __name__ == '__main__':
    unittest.main()