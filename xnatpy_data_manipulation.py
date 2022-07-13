import xnat

session = xnat.connect('http://vm204-misit.informatik.uni-augsburg.de', user='admin', password='admin')


def create_project(project_name):
        session.classes.ProjectData(parent=session, name=project_name)

def delete_project(project_name):
        session.delete('/data/projects/' + project_name)

def get_all_projects():
        return session.projects

def import_file_into_project(filepath, project_name):
        projectLabel = 'test3'
        subjectLabel = 'sub0001'
        # experimentLabel = subjectLabel + '_exp0001'
        # session.put(path='/data/projects/' + project_name + '/resources', files={'name': filepath, 'fileobj': filepath, 'content_type': 'JPEG'})
        # session.upload_file(uri='/data/projects/' + project_name + '/resources', path=filepath, content_type='application/JPEG')
        #session.services.import_(filepath, project=projectLabel, subject=subjectLabel, content_type="application/dicom", destination="/archive")

# create_project('test4')
# delete_project('test4')
# print(get_all_projects())
# print(session.projects["test3"].resources[0].files[0])
#import_file_into_project('/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm', 'test3')

session.disconnect()