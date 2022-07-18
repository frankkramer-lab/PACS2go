import os
from tempfile import TemporaryDirectory
import zipfile
from pyxnat import Interface
from PIL import Image
import uuid


def create_project(interface,name):
        project = interface.select.project(name)
        if project.exists() != True:
                project.create()


def delete_project(interface,name):
        project = interface.select.project(name)
        if project.exists():
                project.delete()

def get_all_projects(interface):
        return interface.select.projects().get()


def get_project_subjects(interface,name):
        return interface.select.project(name).subjects().get()


def insert_zip_into_project(interface, project_name, file_path):
        if zipfile.is_zipfile(file_path):
                with TemporaryDirectory() as tempdir:
                        with zipfile.ZipFile(file_path) as z:
                                z.extractall(tempdir)
                                dir_path = os.path.join(tempdir, os.listdir(tempdir)[0])
                                for f in os.listdir(os.path.join(tempdir, os.listdir(tempdir)[0])): 
                                        #TODO: create new dir for each upload ? currently jpegs are all uploaded to the xnat-dir(resource) 'JPEG' 
                                        insert_file_into_project(interface, project_name, os.path.join(dir_path, f))
                        

def insert_file_into_project(interface, project_name, file_path):
        project = interface.select.project(project_name)
        file_id = str(uuid.uuid4())
        if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                project.resource('JPEG').file(file_id + '.jpeg').insert(file_path, content='image', format='JPEG', tags='image jpeg')
        if file_path.endswith('.json'):
                project.resource('JSON').file(file_id + '.json').insert(file_path, content='metadata', format='JSON', tags='metadata')
        if file_path.endswith('.nii'):
                project.resource('NIFTI').file(file_id + '.nii').insert(file_path, content='image', format='NIFTI', tags='image nifti')
        # TODO: upload dicom with subject/experiment data structure 
        # if file_path.endswith('.dcm'):
        #         project.resource('DICOM').file(file_id + '.dcm').insert(file_path, content='image', format='DICOM', tags='image dicom')
        return file_id


def remove_file_from_project(interface, project_name, file_name, resource_name):
        file = interface.select.project(project_name).resource(resource_name).file(file_name)
        if file.exists():
                file.delete()

# TODO: remove xnat-dir(resource) from project
                
""" 
def show_jpeg():
        project = interface.select.project('test3')
        file = project.resource('JPEG').files().first()
        print(file.get())
        image = Image.open(file.get())
        image.show() """
