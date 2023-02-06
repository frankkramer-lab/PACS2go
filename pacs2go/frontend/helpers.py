import base64
from io import BytesIO
from flask_login import current_user
from flask import session

import dash

from pacs2go.data_interface.pacs_data_interface import Connection

server_url = "http://xnat-web:8080"

colors = {
    'background': '#FFFFFF',
    'text': '#000000',
    'sage': '#8cb897',
    'links': '#2d9e2b'
}

def get_connection():
    if current_user.is_authenticated:
        user = current_user.id
        session_id = session.get("session_id")
        connection_type = "XNAT"
        return Connection(server=server_url, username=user, session_id=session_id, kind=connection_type)
    else:
        pass

 
## LOGIN utils

restricted_page = {}

def require_login(page):
    # Without this only the home address ending in "/" requires a login
    restricted_page[''] = True
    # All pages require login
    for pg in dash.page_registry:
        if page == pg:
            restricted_page[dash.page_registry[pg]['path']] = True


## IMAGE REPRESENATION utils

# from: https://stackoverflow.com/questions/60712647/displaying-pil-images-in-dash-plotly
# usage: html.Img(id="my-img",className="image", width="100%",  src="data:image/png;base64, " + pil_to_b64(pil_img))
def pil_to_b64(im, enc_format="png", **kwargs):
    """
    Converts a PIL Image into base64 string for HTML displaying
    :param im: PIL Image object
    :param enc_format: The image format for displaying. If saved the image will have that extension.
    :return: base64 encoding
    """

    buff = BytesIO()
    im.save(buff, format=enc_format, **kwargs)
    encoded = base64.b64encode(buff.getvalue()).decode("utf-8")

    return encoded
