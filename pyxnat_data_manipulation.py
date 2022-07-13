from pyxnat import Interface
from PIL import Image
import uuid

interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                          user='admin',
                          password='admin')


def create_project(name):
        project = interface.select.project(name)
        if project.exists() != True:
                project.create()


def delete_project(name):
        project = interface.select.project(name)
        if project.exists() == True:
                project.delete()


def get_all_projects():
        return interface.select.projects().get()


def get_project_subjects(name):
        return interface.select.project(name).subjects().get()


def insert_file_into_project(project_name, file_path):
        project = interface.select.project(project_name)
        file_id = str(uuid.uuid4())
        if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                project.resource('JPEG').file(file_id + '.jpeg').insert(file_path,content='image',format='JPEG',tags='image test')
        if file_path.endswith('.json'):
                project.resource('JSON').file(file_id + '.json').insert(file_path,content='metadata',format='JSON',tags='metadata')
        return file_id


def remove_file_from_project(project_name, file_name, resource_name):
        file = interface.select.project(project_name).resource(resource_name).file(file_name)
        print(file)
        file.delete()
                

def show_jpeg():
        project = interface.select.project('test3')
        file = project.resource('JPEG').files().first()
        print(file.get())
        image = Image.open(file.get())
        image.show()



# insert_file_into_project('test3', '/home/main/Desktop/pacs2go/pacs2go/test_data/pathology_images/Case-3-A15-25441-4885.jpg') # absoluten Pfad angeben!!
# insert_file_into_project('test3', '/home/main/Desktop/pacs2go/pacs2go/test_data/example_1.json')

#file = insert_file_into_project('test', '/home/main/Desktop/pacs2go/pacs2go/test_data/example_1.json')
#print(file)
# remove_file_from_project('test3', 'fe2e183c-b1ac-4ba3-8b3e-784d4d223f25.json', 'JSON')

interface.disconnect()