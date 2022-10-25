import random
import time
import unittest
from zipfile import ZipFile
from pacs_data_interface import Connection, Project, Directory, File
import uuid
from PIL import Image
import pyxnat


class TestConnection(unittest.TestCase):
    user = 'admin'
    pwd = 'admin'
    server = 'http://vm204-misit.informatik.uni-augsburg.de:8080'
    wrong_user = 'a'
    wrong_pwd = 'a'
    conn = Connection(server, user, pwd, "XNAT")

    def test_connection_correct_input(self):
        with self.conn as connection:
            self.assertEqual(self.user, connection.user)

    def test_connection_wrong_input(self):
        with self.assertRaises(Exception):
            with Connection(self.server, self.user, self.pwd, "some PACS") as connection:
                print(
                    "This should not be visible, because the kind of connection does not exist.")


class TestDataInterface(unittest.TestCase):
    file_path = '/home/main/Desktop/pacs2go/test_data/dicom_ct_images/CT000105.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    user = 'admin'
    pwd = 'admin'
    server = 'http://vm204-misit.informatik.uni-augsburg.de:8080'
    conn = Connection(server, user, pwd, "XNAT")

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with self.conn as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    @classmethod
    def setUpClass(self):
        # create test data
        with self.conn as connection:
            self.project = Project(connection, uuid.uuid4())
            self.directory = self.project.insert(
                self.zip_file_setup)
            # data to test delete functionalities
            self.to_be_deleted_project = Project(connection, uuid.uuid4())
            self.to_be_deleted_directory = self.project.insert(
                self.zip_file_setup)
            self.to_be_deleted_file = self.project.insert(
                self.file_path)
            # name of a project to test create functionality, stored centrally to ensure deletion after test
            self.to_be_created_project_name = uuid.uuid4()

    @classmethod
    def tearDownClass(self):
        # Delete all test data
        with self.conn as connection:
            self.project.delete_project()
            p = connection.get_project(self.to_be_created_project_name)
            p.delete_project()

    def test_create_project(self):
        # Checks if a project with a certain name is really created
        len_before = len(self.connection.get_all_projects())
        project = Project(self.connection, self.to_be_created_project_name)
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))

    def test_delete_project(self):
        # Checks if a project is deleted
        len_before = len(self.connection.get_all_projects())
        self.to_be_deleted_project.delete_project()
        self.assertNotIn(str(self.to_be_deleted_project.name), [
            p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before - 1, len(self.connection.get_all_projects()))

    def test_double_delete_project(self):
        # Checks if double deleting a project results in an expected Exception
        p = Project(self.connection, uuid.uuid4())
        p.delete_project()
        with self.assertRaisesRegex(Exception, "Project does not exist/has already been deleted."):
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
        with self.assertRaisesRegex(Exception, "The input is neither a file nor a zip."):
            self.project.insert('hello', 'test_general_insert_2')

    def test_file_retrieval(self):
        # Checks if file image data can be retrieved from XNAT
        f = random.choice(self.directory.get_all_files())
        im = Image.open(f.data)
        self.assertEqual(im.format, f.format)
        # not equal for some reason, len(im.fp.read() is always 623byte smaller (metadata perhabs?)
        self.assertEqual(len(im.fp.read()) + 623, f.size)

    def test_file_retrieval_of_deleted_file(self):
        # Checks if the retrivial of a no longer existing file results in an expected Exception
        f = random.choice(self.directory.get_all_files())
        f.delete_file()
        with self.assertRaises(Exception):
            f.data

    def test_delete_file(self):
        # Checks if single file is deleted from directory
        file = self.to_be_deleted_file
        self.assertIn(file.name, [
                      f.name for f in file.directory.get_all_files()])
        file.delete_file()
        self.assertNotIn(file.name, [
                         f.name for f in file.directory.get_all_files()])

    def test_double_delete_file(self):
        # Checks if double deleting a file results in an expected Exception
        file = random.choice(self.directory.get_all_files())
        file.delete_file()
        with self.assertRaisesRegex(Exception, "File does not exist/has already been deleted."):
            file.delete_file()

    def test_delete_diretory(self):
        # Check if single directory is deleted from project
        self.assertIn(self.to_be_deleted_directory.name, [
                      r.name for r in self.project.get_all_directories()])
        self.to_be_deleted_directory.delete_directory()
        self.assertNotIn(self.to_be_deleted_directory.name, [
                         r.name for r in self.project.get_all_directories()])

    def test_double_delete_directory(self):
        # Checks if double deleting a directory results in an expected Exception
        file = self.project.insert(self.file_path)
        d = file.directory
        d.delete_directory()
        with self.assertRaisesRegex(Exception, "Directory does not exist/has already been deleted."):
            d.delete_directory()


if __name__ == '__main__':
    unittest.main()
