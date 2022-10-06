import unittest
from pacs_data_interface import Connection
import uuid

class TestDataInterface(unittest.TestCase):
    file_path = '/home/main/Desktop/pacs2go/test_data/dicom_ct_images/CT000105.dcm'
    zip_file_setup = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    zip_file_test = '/home/main/Desktop/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
    user = 'admin'
    pwd = 'admin'
    server = 'http://vm204-misit.informatik.uni-augsburg.de:8080'
    conn = Connection(server, user, pwd, "XNAT") #this !!!!

    # connect to XNAT for all tests (executed for each testrun)
    def run(self, result=None):
        with self.conn as connection:
            self.connection = connection
            super(TestDataInterface, self).run(result)

    def test_connection(self):
        u = str(self.conn.user)
        self.assertEqual(u, "admin")



if __name__ == '__main__':
    unittest.main()