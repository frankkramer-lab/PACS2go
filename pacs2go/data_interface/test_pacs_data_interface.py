import unittest
from pacs_data_interface import Connection, Project
import uuid

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

    def test_connection(self):
        u = str(self.connection.user)
        self.assertEqual(u, "admin")

    def test_create_project(self):
        # Checks if a project with a certain name is really created
        len_before = len(self.connection.get_all_projects())
        project = Project(self.connection, uuid.uuid4())
        self.assertIn(str(project.name), [
                      p.name for p in self.connection.get_all_projects()])
        self.assertEqual(
            len_before + 1, len(self.connection.get_all_projects()))
        project.delete_project()
    



if __name__ == '__main__':
    unittest.main()