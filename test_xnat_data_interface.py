import unittest
import resource
from pyxnat import Interface
from xnat_pacs_data_interface import XNAT, XNATFile, XNATProject, XNATResource
import uuid
from PIL import Image


class TestDataInterface(unittest.TestCase):
    file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm'
    zip_file = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    project_name = 'test'
    user = 'admin'
    pwd = 'admin'

    # connect to XNAT for all tests

    def run(self, result=None):
        with XNAT(self.user, self.pwd) as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    def test_create_delete_project(self):
        len_before = len(self.connection.get_all_projects())
        project = XNATProject(self.connection, uuid.uuid4())
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))
        project.delete_project()
        self.assertEqual(
            len_before, len(self.connection.get_all_projects()))

    

if __name__ == '__main__':
    unittest.main()
