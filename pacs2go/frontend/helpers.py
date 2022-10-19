from pacs2go.data_interface.pacs_data_interface import Connection

colors = {
    'background': '#FFFFFF',
    'text': '#000000',
    'sage': '#8cb897',
    'links': '#2d9e2b'
}


def get_connection():
    server = 'http://xnat-web:8080'
    user = "admin"
    pwd = "admin"
    connection_type = "XNAT"
    return Connection(server, user, pwd, connection_type)
