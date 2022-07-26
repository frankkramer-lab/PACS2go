import resource
from pyxnat import Interface
from xnat_data_interface import XNAT, XNATFile, XNATProject, XNATResource
import uuid

user = 'admin'
password = 'admin'
file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm' # absoluten Pfad angeben!!
zip_file = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'
zip_file_2 = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images.zip'
project_name = 'test'

def test_create_delete_project(connection):
        project_name = uuid.uuid4()
        project = XNATProject(connection, project_name)
        if str(project_name) in connection.get_all_projects():
                print('Successful project creation.' + ' All projects: ' + str(connection.get_all_projects()))
                project.delete_project()
                if not str(project_name) in connection.get_all_projects():
                        print('Successful project deletion.' + ' Remaining projects: ' + str(connection.get_all_projects()))
                else:
                        print("Failed project deletion.")
        else:
                print("Failed project creation.")


def test_insert_zip_into_project(connection):
        project = XNATProject(connection, project_name)
        print(project.name)
        project.insert_zip_into_project(zip_file_2)

def test_insert_file_into_project(connection):
        project = XNATProject(connection, project_name)
        print(project.name)
        project.insert_file_into_project(file)

def test_retrieve_file(connection):
        file = connection.retrieve_file("test3", "2022-07-23-13-03-33", "bebd60bc-7d92-4c9c-8939-c3aa866d0ae2.jpeg")
        print(file.id())       

def test_retrieve_all_files_from_project_resource(connection):
        files = connection.retrieve_all_files_from_project_resource("test3", "2022-07-23-13-03-33")
        print(files)

def test_remove_file_from_project(connection):
        file_id = connection.insert_file_into_project(project_name, file, "2022-07-23-13-03-33")
        print(connection.get_all_resources_from_project(project_name))
        print(len(connection.retrieve_all_files_from_project_resource(project_name, "2022-07-23-13-03-33")))
        connection.remove_file_from_project(project_name, "2022-07-23-13-03-33", file_id)
        print(len(connection.retrieve_all_files_from_project_resource(project_name, "2022-07-23-13-03-33")))

def test_remove_resource_dir(connection):
        project = XNATProject(connection, project_name)
        resource_name = uuid.uuid4()
        resource = XNATResource(project, "2022-07-24-19-02-10")
        print(len(project.get_resources()))
        resource.remove_resource()
        print(len(project.get_resources()))


with XNAT(user, password) as connection:
        #test_create_delete_project(connection)
        #test_insert_zip_into_project(connection)
        #test_insert_file_into_project(connection)
        #print(connection.get_all_projects())
        #test_remove_resource_dir(connection)
        #test_retrieve_file(connection)
        #test_retrieve_all_files_from_project_resource(connection)
        #test_remove_file_from_project(connection)
        #print(connection.get_project("test").user_role('admin'))
        project = XNATProject(connection, project_name)
        resource = XNATResource(project, "2022-07-25-15-38-06")
        file = XNATFile(resource, "a06551bd-c9fe-4f20-b1dc-40c2d96c6d94.dcm")
        print(file.__dir__())


