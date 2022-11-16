import random
import time
import unittest
import uuid
from zipfile import ZipFile

import pyxnat
from PIL import Image
from xnat_pacs_data_interface import XNAT
from xnat_pacs_data_interface import XNATProject


class TestConnection(unittest.TestCase):
    user = 'admin'
    pwd = 'admin'
    server = 'http://vm204-misit.informatik.uni-augsburg.de:8080'
    wrong_user = 'a'
    wrong_pwd = 'a'

    def test_connection_correct_input(self):
        with XNAT(self.server, self.user, self.pwd) as connection:
            self.assertTrue(type(connection.interface) ==
                            pyxnat.core.interfaces.Interface)
            self.assertEqual(self.user, connection.interface._user)

    def test_connection_wrong_input(self):
        with self.assertRaises(Exception):
            with XNAT(self.server, self.wrong_user, self.wrong_pwd) as connection:
                print(
                    "This should not be visible, because username and password are wrong")


class TestDataInterface(unittest.TestCase):
    file_path = '/home/main/Desktop/pacs2go/test_data/dicom_ct_images/CT000105.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    user = 'admin'
    pwd = 'admin'
    server = 'http://vm204-misit.informatik.uni-augsburg.de:8080'

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with XNAT(self.server, self.user, self.pwd) as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    @classmethod
    def setUpClass(self):
        # create test data
        with XNAT(self.server, self.user, self.pwd) as connection:
            self.project = XNATProject(connection, str(uuid.uuid4()))
            self.directory = self.project.insert_zip_into_project(
                self.zip_file_setup)
            # data to test delete functionalities
            self.to_be_deleted_project = XNATProject(connection, str(uuid.uuid4()))
            self.to_be_deleted_directory = self.project.insert_zip_into_project(
                self.zip_file_setup)
            self.to_be_deleted_file = self.project.insert_file_into_project(
                self.file_path)
            # name of a project to test create functionality, stored centrally to ensure deletion after test
            self.to_be_created_project_name = uuid.uuid4()

    @classmethod
    def tearDownClass(self):
        # Delete all test data
        with XNAT(self.server, self.user, self.pwd) as connection:
            self.project.delete_project()
            p = connection.get_project(str(self.to_be_created_project_name))
            p.delete_project()

    def test_create_project(self):
        # Checks if a project with a certain name is really created
        len_before = len(self.connection.get_all_projects())
        project = XNATProject(self.connection, str(self.to_be_created_project_name))
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
        p = XNATProject(self.connection, str(uuid.uuid4()))
        p.delete_project()
        with self.assertRaisesRegex(Exception, "Project does not exist/has already been deleted."):
            p.delete_project()

    def test_insert(self):
        # Checks if the general insert function behaves as expected (= upload zip as directory and file into directory)
        dir = self.project.insert(self.zip_file_test, 'test_general_insert_1')
        self.assertIn(dir.name, [
                      r.name for r in self.project.get_all_directories()])
        file = self.project.insert(self.file_path, dir.name)
        self.assertIn(
            file.name, [f.name for f in dir.get_all_files()])

    def test_insert_invalid_input(self):
        # Checks if wrong input raises the expected Exception
        with self.assertRaisesRegex(Exception, "The input is neither a file nor a zip."):
            self.project.insert('hello', 'test_general_insert_2')

    def test_insert_zip(self):
        # Checks if correct number of files was uploaded and if a new directory was created
        len_before = len(self.project.get_all_directories())
        with ZipFile(self.zip_file_test) as zipfile:
            number_of_files_before = len(zipfile.namelist())
        start_time = time.time()
        directory = self.project.insert_zip_into_project(
            self.zip_file_test, 'test_zip_insert_1')
        end_time = time.time()
        duration = end_time - start_time
        print("Duration of zip upload: " + str(duration))
        self.assertEqual(
            len_before + 1, len(self.project.get_all_directories()))
        self.assertIn(directory.name, [
                      r.name for r in self.project.get_all_directories()])
        self.assertEqual(number_of_files_before,
                         len(directory.get_all_files()))

    def test_insert_invalid_zip(self):
        # Checks if a non-zip file raises an excpetion when one tries to upload it as a zip
        with self.assertRaisesRegex(Exception, "The input is not a zipfile."):
            self.project.insert_zip_into_project(
                self.file_path, 'test_zip_insert_2')

    def test_insert_file(self):
        # Checks if upload of single file with and without specified directory is successful
        len_before = len(self.directory.get_all_files())
        file = self.project.insert_file_into_project(
            self.file_path, self.directory.name)
        self.assertIn(
            file.name, [f.name for f in self.directory.get_all_files()])
        self.assertEqual(len_before + 1, len(self.directory.get_all_files()))
        # test file upload without specified directory (new directory will be created)
        file = self.project.insert_file_into_project(self.file_path)
        self.assertIn(
            file.name, [f.name for f in file.directory.get_all_files()])

    def test_insert_unsupported_file(self):
        # Checks if unsupported files are handeled correctly -> exception is raised
        with self.assertRaisesRegex(Exception, "This file type is not supported."):
            self.project.insert_file_into_project(
                "/home/main/Desktop/pacs2go/test_data/103.bmp", 'test_file_insert_2')

    def test_insert_invalid_file(self):
        # Checks if something that is not a file raises an exception
        with self.assertRaisesRegex(Exception, "The input is not a file."):
            self.project.insert_file_into_project(
                "hello", 'test_file_insert_3')

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
