from pyxnat import Interface
from xnat_data_interface import XNAT
import uuid

user = 'admin'
password = 'admin'
file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm' # absoluten Pfad angeben!!
zip_file = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'


def test_create_delete_project(connection):
        project_name = uuid.uuid4()
        connection.create_project(project_name)
        if str(project_name) in connection.get_all_projects():
                print('Successful project creation.' + ' All projects: ' + str(connection.get_all_projects()))
                connection.delete_project(str(project_name))
                if not str(project_name) in connection.get_all_projects():
                        print('Successful project deletion.' + ' Remaining projects: ' + str(connection.get_all_projects()))
                else:
                        print("Failed project deletion.")
        else:
                print("Failed project creation.")


connection = XNAT(user, password)
test_create_delete_project(connection)
#print(connection.get_all_projects())
connection.free()
