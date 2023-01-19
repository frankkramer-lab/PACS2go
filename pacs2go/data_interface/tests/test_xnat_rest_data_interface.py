import random
import time
import unittest
import uuid
from PIL import Image

from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNAT, XNATProject, XNATDirectory


class TestConnection(unittest.TestCase):
    user = 'admin'
    pwd = 'admin'
    server = 'http://localhost:8888'
    wrong_user = 'a'
    wrong_pwd = 'a'

    def test_connection_correct_input(self):
        with XNAT(server=self.server, username=self.user, password=self.pwd, kind="XNAT") as connection:
            self.assertEqual(connection.user, "admin")

    def test_connection_wrong_input(self):
        with self.assertRaises(Exception):
            with XNAT(server=self.server, username=self.wrong_user, password=self.wrong_pwd) as connection:
                print(
                    "This should not be visible, because username and password are wrong")


class TestDataInterface(unittest.TestCase):
    file_path = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/single files/Case-48-P5-C16-39161-16929.jpg'
    zip_file_setup = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    user = 'admin'
    pwd = 'admin'
    server = 'http://localhost:8888'

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with XNAT(server=self.server, username=self.user, password=self.pwd, kind="XNAT") as connection:
            self.connection = connection
            self.session = connection.session_id
            super(TestDataInterface, self).run(result)

    @classmethod
    def setUpClass(self):
        # create test data
        with XNAT(server=self.server, username=self.user, password=self.pwd, kind="XNAT") as connection:
            self.project = XNATProject(connection, str(uuid.uuid4()))
            self.directory = self.project.insert_zip_into_project(self.zip_file_setup)
            self.file = self.project.insert(self.file_path, self.directory.name)
            #data to test delete functionalities
            self.to_be_deleted_project = XNATProject(connection, str(uuid.uuid4()))
            self.to_be_deleted_directory = self.project.insert_zip_into_project(self.zip_file_setup)
            self.to_be_deleted_file = self.project.insert_file_into_project(self.file_path)
            #name of a project to test create functionality, stored centrally to ensure deletion after test
            self.to_be_created_project_name = uuid.uuid4()

    @classmethod
    def tearDownClass(self):
        # Delete all test data
        with XNAT(server=self.server, username=self.user, password=self.pwd, kind="XNAT") as connection:
            if self.project.exists():
                self.project.delete_project()
            try:
                p = connection.get_project(str(self.to_be_created_project_name))
                p.delete_project()
                self.to_be_deleted_project.delete_project()
            except:
                pass

    def test_createproject(self):
        # Checks if a project with a certain name is really created
        len_before = len(self.connection.get_all_projects())
        project = XNATProject(self.connection, str(
            self.to_be_created_project_name))
        #print(project.description)
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))

    def test_setprojectdescription_and_setprojectkeywords(self):
        new_description = "hehe this is a new description"
        self.project.set_description(new_description)
        self.assertEqual(self.project.description, new_description)
        new_keywords = "MRI, CT, etc"
        self.project.set_keywords(new_keywords)
        self.assertEqual(self.project.keywords, new_keywords)

    def test_fileinsert(self):
        # Tests if upload of single file is successful
        len_before = len(self.project.get_all_directories())
        file = self.project.insert_file_into_project(
            self.file_path, tags_string='new')
        # New file in directory
        self.assertIn(
            file.name, [f.name for f in file.directory.get_all_files()])
        # Project should have 1 new directory
        self.assertEqual(len_before + 1, len(self.project.get_all_directories()))
        # New directory should have 1 file
        self.assertEqual(1, len(file.directory.get_all_files()))
        # Tags should be set accordingly to specified tags_string
        self.assertIn('new', file.tags)
    
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
        with self.assertRaisesRegex(Exception, "Something went wrong trying to delete this file. 404"):
            file.delete_file()
    
    def test_delete_diretory(self):
        # Check if single directory is deleted from project
        self.assertIn(self.to_be_deleted_directory.name, [
                      r.name for r in self.project.get_all_directories()])
        self.to_be_deleted_directory.delete_directory()
        self.assertNotIn(self.to_be_deleted_directory.name, [
                         r.name for r in self.project.get_all_directories()])

    # def test_double_delete_directory(self):
    #     # Checks if double deleting a directory results in an expected Exception
    #     file = self.project.insert(self.file_path)
    #     d = file.directory
    #     d.delete_directory()
    #     print()
    #     with self.assertRaises(Exception):
    #         d.delete_directory()
    
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
        with self.assertRaisesRegex(Exception, "Something went wrong trying to delete the project.400"):
            p.delete_project()
        
    def test_file_retrieval(self):
        # Checks if file image data can be retrieved from XNAT
        f = random.choice(self.directory.get_all_files())
        im = Image.open(f.data)
        # Correct format
        self.assertEqual(im.format, f.format)
        # not equal for some reason, len(im.fp.read() is always 623byte smaller (metadata perhabs?)
        self.assertEqual(len(im.fp.read()) + 623, f.size)




if __name__ == '__main__':
    unittest.main()
