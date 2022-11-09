import base64
from io import BytesIO

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
