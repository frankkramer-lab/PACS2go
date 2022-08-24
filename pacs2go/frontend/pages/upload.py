#from PIL import Image
from dash import register_page, html, dcc, callback, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT, XNATProject

register_page(__name__, title='PACS2go 2.0', path='/upload')

server = 'http://xnat-web:8080'

# TODO: input fields so user can specify what project (and directory) the data is uploaded to 

def file_input():
    return html.Div(
        [
            dbc.Label(""),
            dbc.Input(id="file-input", type="file", value=""),
            dbc.FormFeedback("That looks like a correct format :)", type="valid"),
            dbc.FormFeedback(
                "Sorry, we only accept JPEG, PNG, DICOM, NIFTI and JSON at the moment...",
                type="invalid",
            ),
            html.Div(id='image-preview-and-upload-button'),
        ]
    )

def parse_contents(file):
    # display image preview and filename
    if file.endswith('.jpg') or file.endswith('.jpeg'):
        img = Image.open(file)
        return dbc.Card(
            [
                dbc.CardBody(html.P(file, className="card-text")),
                dbc.CardImg(src=img, bottom=True)
            ])
    else:
        return html.H5(file)


# @callback(Output('output-image-preview', 'children'),
#           Input('upload-image', 'contents'),
#           State('upload-image', 'filename'))
# def update_output(contents, filename):
#     # get selected data (preview it) and display upload button
#     if contents is not None:
#         children = dbc.Row(
#             [
#                 dbc.Col([parse_contents(contents, filename)]),
#                 dbc.Col([dbc.Button("Upload to XNAT", id="click-upload", size="lg", color="success", className="col-6 mx-auto mb-3"),
#                         # placeholder for successful upload message
#                          html.Div(id='output-upload')]),
#             ], className="mt-3"
#         ),
#         return children


# @callback(
#     Output('output-upload', 'children'),
#     Input('click-upload', 'n_clicks'),
#     # State because only button click should trigger callback
#     State('upload-image', 'contents'),
#     State('upload-image', 'filename')
# )
# def upload_to_xnat(btn, contents, filename):
#     # triggered by clicking on the upload button
#     if "click-upload" == ctx.triggered_id:
#         # TODO: implement xnat upload for zip (tempfile can not be recognized as zipfile)!! 
#         # TODO: test different formats through frontend
#         with tempfile.NamedTemporaryFile(suffix=filename) as tf:
#             try:
#                 # https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
#                 data = contents.encode("utf8").split(b";base64,")[1]
#                 tf.write(base64.b64decode(data))
#                 with XNAT(server, 'admin', 'admin') as connection:
#                     # upload to XNAT server
#                     XNATProject(
#                         connection, 'test6').insert_file_into_project(tf.name)
#                 return html.Div("Upload successful")
#             except Exception as err:
#                 # TODO: differentiate between different exceptions
#                 return html.Div("Upload unsuccessful: " + str(err))
#     return html.Div("")



@callback(
    [Output("file-input", "valid"), Output("file-input", "invalid")],
    [Input("file-input", "value")],
)
def check_validity(file):
    # check if file is accepted and if so display upload button
    if file:
        if file.endswith('.json') or file.endswith('.jpeg') or file.endswith('.jpg') or file.endswith('.png') or file.endswith('.nii') or file.endswith('.dcm'): 
            parse_contents(file)
            return True, False
        else:
            return False, True
    return False, False



def layout():
    return [html.H1(
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),
        dcc.Markdown(children='Please select a **zip** folder or a single file to upload. \n \n' +
                     'Accepted formats include **DICOM**, **NIFTI**, **JPEG** and **JSON**.'),
        file_input()
    ]
