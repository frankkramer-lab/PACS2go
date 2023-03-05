import random
import unittest
import uuid

from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulDeletionException
from pacs2go.data_interface.exceptions.exceptions import WrongUploadFormatException
from pacs2go.data_interface.pacs_data_interface import Connection
from pacs2go.data_interface.pacs_data_interface import Directory
from pacs2go.data_interface.pacs_data_interface import File
from pacs2go.data_interface.pacs_data_interface import Project


class TestConnection(unittest.TestCase):
    user = 'admin'
    pwd = 'admin'
    server = 'http://localhost:8888'
    wrong_user = 'a'
    wrong_pwd = 'a'
    conn = Connection(server, user, pwd, kind ="XNAT")

    def test_connection_correct_input(self):
        with self.conn as connection:
            self.assertEqual(self.user, connection.user)

    def test_connection_wrong_input(self):
        with self.assertRaises(FailedConnectionException):
            with Connection(self.server, self.user, self.pwd, kind= "some PACS") as connection:
                print(
                    "This should not be visible, because the kind of connection does not exist.")


class TestDataInterface(unittest.TestCase):
    file_path = '/home/main/Desktop/pacs2go/test_data/dicom_ct_images/CT000105.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    user = 'admin'
    pwd = 'admin'
    server = 'http://localhost:8888'
    conn = Connection(server, user, pwd, kind = "XNAT")

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with self.conn as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    @classmethod
    def setUpClass(self):
        # create test data
        with self.conn as connection:
            self.project = Project(connection, str(uuid.uuid4()))
            self.directory = self.project.insert(
                self.zip_file_setup)
            # data to test delete functionalities
            self.to_be_deleted_project = Project(connection, str(uuid.uuid4()))
            self.to_be_deleted_directory = self.project.insert(
                self.zip_file_setup)
            self.to_be_deleted_file = self.project.insert(
                self.file_path, directory_name=self.directory.name)
            self.to_be_double_deleted_file = self.project.insert(
                self.file_path, directory_name=self.directory.name)
            # name of a project to test create functionality, stored centrally to ensure deletion after test
            self.to_be_created_project_name = uuid.uuid4()

    @classmethod
    def tearDownClass(self):
        # Delete all test data
        with self.conn as connection:
            self.project.delete_project()
            p = connection.get_project(str(self.to_be_created_project_name))
            if p:
                p.delete_project()

    def test_create_project(self):
        # Checks if a project with a certain name is really created
        len_before = len(self.connection.get_all_projects())
        project = Project(self.connection, str(self.to_be_created_project_name))
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))

    def test_zdelete_project(self):
        # Checks if a project is deleted
        len_before = len(self.connection.get_all_projects())
        self.to_be_deleted_project.delete_project()
        self.assertNotIn(str(self.to_be_deleted_project.name), [
            p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before - 1, len(self.connection.get_all_projects()))

    def test_zdouble_delete_project(self):
        # Checks if double deleting a project results in an expected Exception
        p = Project(self.connection, str(uuid.uuid4()))
        p.delete_project()
        with self.assertRaises(UnsuccessfulDeletionException):
            p.delete_project()

    def test_insert(self):
        # Checks if the general insert function behaves as expected (= upload zip as directory and file into directory)
        dir: Directory = self.project.insert(self.zip_file_test, 'test_general_insert_1')
        self.assertIn(dir.name, [
                      r.name for r in self.project.get_all_directories()])
        file: File = self.project.insert(self.file_path, dir.name)
        self.assertIn(
            file.name, [f.name for f in dir.get_all_files()])

    def test_insert_invalid_input(self):
        # Checks if wrong input raises the expected Exception
        with self.assertRaises(WrongUploadFormatException):
            self.project.insert('hello', 'test_general_insert_2')

    def test_file_retrieval(self):
        # Checks if file image data can be retrieved from XNAT
        f = random.choice(self.directory.get_all_files())
        im = f.data
        self.assertEqual(len(im), f.size)

    def test_delete_file(self):
        # Checks if single file is deleted from directory
        file = self.to_be_deleted_file
        self.assertIn(file.name, [
                      f.name for f in file.directory.get_all_files()])
        file.delete_file()
        self.assertNotIn(file.name, [
                         f.name for f in file.directory.get_all_files()])

    def test_xdouble_delete_file(self):
        # Checks if double deleting a file results in an expected Exception
        file = File(self.to_be_double_deleted_file.directory, self.to_be_double_deleted_file.name)
        file.delete_file()
        with self.assertRaises(UnsuccessfulDeletionException):
            file.delete_file()

    def test_ydelete_diretory(self):
        # Check if single directory is deleted from project
        self.assertIn(self.to_be_deleted_directory.name, [
                      r.name for r in self.project.get_all_directories()])
        self.to_be_deleted_directory.delete_directory()
        self.assertNotIn(self.to_be_deleted_directory.name, [
                         r.name for r in self.project.get_all_directories()])


if __name__ == '__main__':
    unittest.main()
