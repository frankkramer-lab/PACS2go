import re
import unittest
import resource
from pyxnat import Interface
from xnat_pacs_data_interface import XNAT, XNATFile, XNATProject, XNATResource
import uuid
from PIL import Image


class TestDataInterface(unittest.TestCase):
    file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_100.zip'
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
            self.resource_name = self.project.insert_zip_into_project(self.zip_file_setup)
            self.resource = XNATResource(self.project, self.resource_name)
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
        resource_name = self.project.insert_zip_into_project(self.zip_file_test)
        self.assertIn(resource_name, [r.name for r in self.project.get_all_directories()])


if __name__ == '__main__':
    unittest.main()
