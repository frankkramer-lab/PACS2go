import time
import unittest
from zipfile import ZipFile
from xnat_pacs_data_interface import XNAT, XNATFile, XNATProject, XNATResource
import uuid
from PIL import Image


class TestDataInterface(unittest.TestCase):
    file_test = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    project_name = uuid.uuid4()
    user = 'admin'
    pwd = 'admin'

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with XNAT(self.user, self.pwd) as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    @classmethod
    def setUpClass(self):
        # create test data
        with XNAT(self.user, self.pwd) as connection:
            self.project = XNATProject(connection, self.project_name)
            self.resource = self.project.insert_zip_into_project(self.zip_file_setup)
            self.file = self.resource.get_all_files()[0]

    @classmethod
    def tearDownClass(self):
        # Delete all test data
        with XNAT(self.user, self.pwd) as connection:
            for d in self.project.get_all_directories():
                for f in d.get_all_files():
                    f.delete_file()
                d.delete_directory()
            self.project.delete_project()

    # checks if a project with a certain name is really created and deleted
    def test_create_delete_project(self):
        len_before = len(self.connection.get_all_projects())
        project = XNATProject(self.connection, uuid.uuid4())
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))
        project.delete_project()
        self.assertNotIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before, len(self.connection.get_all_projects()))

    # checks if correct number of files was uploaded and if a new directory was created
    def test_insert_zip(self):
        with ZipFile(self.zip_file_test) as zipfile:
                number_of_files_before = len(zipfile.namelist())
        start_time = time.time()
        resource = self.project.insert_zip_into_project(self.zip_file_test)
        end_time = time.time()
        duration = end_time - start_time
        print(duration)
        self.assertIn(resource.name, [r.name for r in self.project.get_all_directories()])
        self.assertEqual(number_of_files_before, len(resource.get_all_files()))

    # checks if upload of single file with and without specified directory is successful
    def test_insert_file(self):
        len_before = len(self.resource.get_all_files())
        file = self.project.insert_file_into_project(self.file_test, self.resource.name)
        self.assertIn(file.name, [f.name for f in self.resource.get_all_files()])
        self.assertEqual(len_before + 1, len(self.resource.get_all_files()))
        # test file upload without specified directory (new directory will be created)
        file = self.project.insert_file_into_project(self.file_test)
        self.assertIn(file.name, [f.name for f in file.directory.get_all_files()])


    # checks if single file and single directory are deleted
    def test_delete_file_and_directory(self):
        #test deletion of file
        self.assertIn(self.file.name, [f.name for f in self.resource.get_all_files()])
        self.file.delete_file()
        self.assertNotIn(self.file.name, [f.name for f in self.resource.get_all_files()])
        #test deletion of directory (resource)
        self.assertIn(self.resource.name, [r.name for r in self.project.get_all_directories()])
        self.resource.delete_directory()
        self.assertNotIn(self.resource.name, [r.name for r in self.project.get_all_directories()])

    


    

if __name__ == '__main__':
    unittest.main()
