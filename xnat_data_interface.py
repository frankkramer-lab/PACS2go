from pyxnat import Interface



#---------------------------------------------#
#          XNAT data interface class          #
#---------------------------------------------#
class XNAT:
        def __init__(self, username, password):
                # connect to xnat server
                self.interface = Interface(server='http://vm204-misit.informatik.uni-augsburg.de',
                          user=username,
                          password=password)

        # disconnect from xnat server to quit session
        def free(self):
                
                self.interface.disconnect()
                print("successful disconnect from server")

        # get list of project identifiers       
        def get_all_projects(self):
                return self.interface.select.projects().get()

        # create new project with identifier 'name'
        def create_project(self,name):
                project = self.interface.select.project(name)
                if project.exists() != True:
                        project.create()

        # delete project with identifier 'name'
        def delete_project(self,name):
                project = self.interface.select.project(name)
                if project.exists():
                        project.delete()

        


    
