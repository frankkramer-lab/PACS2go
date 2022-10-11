from pacs2go.data_interface.pacs_data_interface import Connection

colors = {
    'background': '#FFFFFF',
    'text': '#000000',
    'sage': '#8cb897'
}

server = 'http://xnat-web:8080'
user = "admin"
pwd = "admin"


def get_connection():
    return Connection(server, user, pwd, "XNAT")