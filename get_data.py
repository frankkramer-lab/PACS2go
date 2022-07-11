from pyxnat import Interface

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


def insert_subject_into_project(name):
        project = interface.select.project(name)
        file_jpg = '/test_data/pathology_images/Case-3-A14-39214-1868.jpg'
        #project.resource('JPEG').file(file_jpg).insert('/tmp/image.jpg')
        subject = "sub001"
        experiment = "sub001_ex"               
        file = project.subject(subject).experiment(experiment).scan("1").resource("JPEG").file(file_jpg)
        file.put(file_jpg, format="JPEG", content=" ", tags=" ")


insert_subject_into_project('test3')
