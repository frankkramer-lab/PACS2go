from pyxnat import Interface
from pyxnat_data_manipulation import insert_file_into_project, insert_zip_into_project, remove_file_from_project, get_all_projects, get_project_subjects, create_project, delete_project

user = 'admin'
password = 'admin'

interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                          user=user,
                          password=password)


file = '/home/main/Desktop/pacs2go/pacs2go/test_data/dicom_ct_images/CT000000.dcm' # absoluten Pfad angeben!!
zip_file = '/home/main/Desktop/pacs2go/pacs2go/test_data/benchmarking/convert/jpegs_25.zip'

# insert_file_into_project(interface, 'test3', file)
# insert_zip_into_project(interface, 'test3', zip_file)
# remove_file_from_project(interface, 'test3', file, 'DICOM')
# print(get_all_projects(interface))

interface.disconnect()