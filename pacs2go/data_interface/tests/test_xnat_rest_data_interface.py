import unittest
import uuid

from pacs2go.data_interface.xnat_rest_pacs_data_interface import XNAT, XNATProject


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
    file_path = '/home/main/Desktop/pacs2go/test_data/dicom_ct_images/CT000105.dcm'
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
            #self.directory = self.project.insert_zip_into_project(self.zip_file_setup)
            # data to test delete functionalities
            #self.to_be_deleted_project = XNATProject(connection, str(uuid.uuid4()))
            #self.to_be_deleted_directory = self.project.insert_zip_into_project(self.zip_file_setup)
            #self.to_be_deleted_file = self.project.insert_file_into_project(self.file_path)
            # name of a project to test create functionality, stored centrally to ensure deletion after test
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
            except:
                pass

    def test_getproject(self):
        # Checks if a project with a certain name is really created
        p = self.connection.get_project("test_keywords_2")
        #print(p.name)

    def test_getallprojects(self):
        p = self.connection.get_all_projects()
        #print(p[0].name)

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



if __name__ == '__main__':
    unittest.main()
