#from PIL import Image
import tempfile
import shutil
import os
from dash import register_page, html, dcc, get_app
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import get_connection
import dash_uploader as du
import uuid


register_page(__name__, title='PACS2go 2.0',
              path_template='/large_upload/<project_name>')

# TODO: upload of large files -> maybe using: https://github.com/np-8/dash-uploader


# setup 
dirpath = tempfile.mkdtemp()
UPLOAD_FOLDER_ROOT = dirpath
du.configure_upload(get_app(), UPLOAD_FOLDER_ROOT)

def upload_tempdir_to_xnat(filename):
    # after dash-uploader upload file to tempdir, upload to xnat and delete tempdir
    project_name = "test_1"
    with get_connection() as connection:
        Project(connection, project_name).insert(filename)
        shutil.rmtree(dirpath)

def get_upload_component(id):
    return du.Upload(
        id=id,
        max_file_size=1800,  # 1800 Mb
        filetypes=['zip', 'jpeg', 'jpg', 'dcm', 'json', 'nii'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


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
        # du uploader
        html.Div(
            [
                get_upload_component(id='dash-uploader'),
                html.Div(id='callback-output'),
            ],),
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

@du.callback(
    output=Output('callback-output', 'children'),
    id='dash-uploader',
)
def get_a_list(filenames):
    filename = filenames[0]
    upload_tempdir_to_xnat(filename)
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return dbc.Card(
            [
                dbc.CardBody(html.P(filename, className="card-text")),
                #dbc.CardImg(src=contents, bottom=True)
            ])
    else:
        return html.H5(filename)

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
