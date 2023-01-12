import unittest

from xnat_rest_pacs_data_interface import XNAT


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

    def test_getproject(self):
        # Checks if a project with a certain name is really created
        p = self.connection.get_project("test_keywords_2")
        print(p)


if __name__ == '__main__':
    unittest.main()
