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


def get_all_projects():
        return interface.select.projects().get()


def get_project_subjects(name):
        return interface.select.project(name).subjects().get()


def insert_file_into_project(name, filename):
        project = interface.select.project(name)
        if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                project.resource('JPEG').file(str(uuid.uuid4()) + '.jpeg').insert(filename,content='image',format='JPEG',tags='image test')
        if filename.endswith('.json'):
                project.resource('JSON').file(str(uuid.uuid4()) + '.json').insert(filename,content='metadata',format='JSON',tags='metadata')
        

""" def show_jpeg():
        project = interface.select.project('test3')
        files = project.resource('JPEG').files().first()
        print(files.get())
        image = Image.open(files.get())
 """
# insert_file_into_project('test3', '/home/main/Desktop/pacs2go/pacs2go/test_data/pathology_images/Case-3-A15-25441-4885.jpg') # absoluten Pfad angeben!!
# insert_file_into_project('test3', '/home/main/Desktop/pacs2go/pacs2go/test_data/example_1.json')
