from pyxnat import Interface
from xnat_data_interface import XNAT
import uuid

user = 'admin'
password = 'admin'
file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm' # absoluten Pfad angeben!!
zip_file = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
project_name = 'test'

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


def test_insert_zip_into_project(connection):
        project_name = connection.get_all_projects()[0]
        print(project_name)
        connection.insert_zip_into_project(project_name, zip_file)
        #TODO: show(retrieve) resource data from project (here: print what's inside the project)-> interface functionality

def test_insert_file_into_project(connection):
        project_name = connection.get_all_projects()[0]
        print(project_name)
        connection.insert_file_into_project(project_name,file)

def test_retrieve_file(connection):
        file = connection.retrieve_file("test3", "2022-07-23-13-03-33", "bebd60bc-7d92-4c9c-8939-c3aa866d0ae2.jpeg")
        print(file)

def test_retrieve_all_files_from_project_resource(connection):
        files = connection.retrieve_all_files_from_project_resource("test3", "2022-07-23-13-03-33")
        print(files)


connection = XNAT(user, password)
#test_create_delete_project(connection)
#test_insert_zip_into_project(connection)
#test_insert_file_into_project(connection)
#print(connection.get_all_projects())
#test_retrieve_file(connection)
#test_retrieve_all_files_from_project_resource(connection)
connection.free()
