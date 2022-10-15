#from PIL import Image
import tempfile
import base64
from dash import register_page, html, dcc, callback, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import get_connection

register_page(__name__, title='PACS2go 2.0',
              path_template='/upload/<project_name>')


# TODO: upload of large files -> maybe using: https://github.com/np-8/dash-uploader


def uploader(passed_project: str):
    # if user navigates directly to upload, project name input field will be empty
    if passed_project == 'none':
        passed_project = ''
    # Upload drag and drop area
    return html.Div([
        dbc.Row([
            dbc.Col(
                # input field value equals project name, if user navigates to upload via a specific project
                [dbc.Label("Project"),
                 dbc.Input(id="project_name", placeholder="Project Name...", required=True, value=passed_project), ]),
            dbc.Col(
                [dbc.Label("Directory"),
                 dbc.Input(id="directory_name",
                           placeholder="Directory Name (optional)"),
                 dbc.FormText("If you choose not to specify the name of the directory, the current date and time will be used",)], className="mb-3")
        ]),
        dcc.Upload(
            id='file-input',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
            },
            # Don't allow multiple files to be uploaded
            multiple=False
        ),
        # placeholder for image preview / upload Button to appear
        html.Div(id='image-preview-and-upload-button'),
    ])


def preview(contents, filename):
    # display image preview and filename
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return dbc.Card(
            [
                dbc.CardBody(html.P(filename, className="card-text")),
                dbc.CardImg(src=contents, bottom=True)
            ])
    else:
        return html.H5(filename)


#################
#   Callbacks   #
#################

@callback(Output('image-preview-and-upload-button', 'children'),
          Input('file-input', 'contents'),
          State('file-input', 'filename'))
def preview_and_upload(contents, filename):
    # get selected data (preview it) and display upload button
    if contents is not None:
        children = dbc.Row(
            [
                dbc.Col([preview(contents, filename)]),
                dbc.Col([dbc.Button("Upload to XNAT", id="click-upload", size="lg", color="success", className="col-6 mx-auto mb-3"),
                        # placeholder for successful upload message
                         html.Div(id='output-upload')]),
            ], className="mt-3"
        ),
        return children


@callback(
    Output('output-upload', 'children'),
    Input('click-upload', 'n_clicks'),
    # State because only button click should trigger callback
    State('file-input', 'contents'),
    State('file-input', 'filename'),
    State('project_name', 'value'),
    State('directory_name', 'value'),
)
def upload_to_xnat(btn, contents, filename, project_name, directory_name):
    # triggered by clicking on the upload button
    if "click-upload" == ctx.triggered_id:
        if project_name:
            project_name = str(project_name).replace(" ", "_")
            # TODO: test different formats through frontend
            with tempfile.NamedTemporaryFile(suffix=filename) as tf:
                try:
                    # https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
                    data = contents.encode("utf8").split(b";base64,")[1]
                    tf.write(base64.b64decode(data))
                    if directory_name:
                        with get_connection() as connection:
                            # upload to XNAT server
                            Project(
                                connection, project_name).insert(tf.name, directory_name)
                    else:
                        with get_connection() as connection:
                            # upload to XNAT server
                            Project(
                                connection, project_name).insert(tf.name)
                    return html.Div("Upload successful")
                except Exception as err:
                    # TODO: differentiate between different exceptions
                    return html.Div("Upload unsuccessful: " + str(err))
        else:
            return html.H5("Please specify Project Name.")
    return html.Div("")


#################
#  Page Layout  #
#################

def layout(project_name=None):
    return [html.H1(
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),
        dcc.Markdown(children='Please select a **zip** folder or a single file to upload. \n \n' +
                     'Accepted formats include **DICOM**, **NIFTI**, **JPEG** and **JSON**.'),
        uploader(project_name)
    ]
