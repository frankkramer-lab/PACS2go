import time
import unittest
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
            self.project.delete_project()

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

    
    def test_insert_zip(self):
        start_time = time.time()
        resource = self.project.insert_zip_into_project(self.zip_file_test)
        end_time = time.time()
        duration = end_time - start_time
        print(duration)
        self.assertIn(resource.name, [r.name for r in self.project.get_all_directories()])

    def test_insert_file(self):
        file = self.project.insert_file_into_project(self.file_test, self.resource.name)
        self.assertIn(file.name, [f.name for f in self.resource.get_all_files()])
        # test file upload without specified directory (new directory will be created)
        file = self.project.insert_file_into_project(self.file_test)
        self.assertIn(file.name, [f.name for f in file.directory.get_all_files()])


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
