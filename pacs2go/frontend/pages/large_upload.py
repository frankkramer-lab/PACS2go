import shutil
import tempfile
import uuid
from typing import List
from typing import Optional

import dash_bootstrap_components as dbc
import dash_uploader as du  # https://github.com/np-8/dash-uploader
from dash import callback
from dash import ctx
from dash import dcc
from dash import get_app
from dash import html
from dash import no_update
from dash import register_page
from dash.dependencies import Input
from dash.dependencies import Output
from dash.dependencies import State

from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection


register_page(__name__, title='Upload - PACS2go',
              path_template='/upload/<project_name>')

# Setup dash-uploader
# Attention: global variables not recommended for multi-user environments
dirpath = tempfile.mkdtemp()
UPLOAD_FOLDER_ROOT = dirpath
du.configure_upload(get_app(), UPLOAD_FOLDER_ROOT)


def get_project_names() -> List[str]:
    # Get List of all project names as html Options
    with get_connection() as connection:
        project_list = []

        for p in connection.get_all_projects():
            project_list.append(html.Option(value=p.name))

        return project_list


def get_upload_component(id: str):
    # dash-uploader Upload component
    return du.Upload(
        id=id,
        max_file_size=1024,  # 1GB
        filetypes=['zip', 'jpeg', 'jpg', 'dcm',
                   'json', 'nii', 'png', 'tiff', 'csv'],
        upload_id=uuid.uuid1(),  # Unique session id
        text='Drag and Drop your file right here! Or click here to select a file!',
        text_completed='Ready for XNAT Upload: ',
    )


def uploader(passed_project: Optional[str]):
    # If user navigates directly to upload, project name input field will be empty
    if passed_project == 'none':
        passed_project = ''
    # Upload drag and drop area
    return html.Div([
        dbc.Row(html.H5([html.B("1."), " Specify the project's name."])),
        dbc.Row([
            dbc.Col(
                # Input field value equals project name, if user navigates to upload via a specific project
                [dbc.Label("Project"),
                 html.Datalist(children=get_project_names(),
                               id='project_names'),
                 dbc.Input(id="project_name", type="text", placeholder="Project Name...",
                           required=True, value=passed_project, list='project_names'),
                 dbc.FormText("If you choose a pre-existent project name, the data will be inserted into this project. Otherwise a new project will be created.")], className="mb-3"),
            dbc.Col(
                [dbc.Label("Directory"),
                 dbc.Input(id="directory_name",
                           placeholder="Directory Name (optional)"),
                 dbc.FormText("If you choose not to specify the name of the directory, the current date and time will be used")], className="mb-3")
        ]),
        dbc.Row(dbc.Col(
                [dbc.Label("Tags - If you wish, you may add tags that describe your files' contents. Please separate each tag by comma."),
                 dbc.Input(id="upload_file_tags",
                           placeholder="File tags like \'CT, Dermatology,...\' (optional)"),
                 dbc.FormText("Tags will be added to every file.")], className="mb-3")),
        dbc.Row(html.H5([html.B("2."), ' Please select a zip folder or a single file to upload.', html.Br(),
                         'Accepted formats include DICOM, NIFTI, JPEG, PNG, TIFF, CSV and JSON.'])),
        dbc.Row(
            [
                get_upload_component(id='dash-uploader'),
                # Placeholder for 'Upload to XNAT' button
                html.Div(id='du-callback-output'),
            ])
    ])


#################
#   Callbacks   #
#################

# Callback for the dash-uploader Upload component -> called when something is uploaded
# Triggers the appearance of an 'Upload to XNAT' button
@du.callback(
    output=[Output('du-callback-output', 'children'),
            Output('filename-storage', 'data')],
    id='dash-uploader',
)
def pass_filename_and_show_upload_button(filenames: List[str]):
    # Get file -> only one file should be in this list bc 'dirpath' is removed after each upload
    filename = filenames[0]
    return [html.Div([
        html.H5([html.B("3."), ' Confirm upload to XNAT.']),
        dbc.Button("Upload to XNAT", id="click-upload",
                   size="lg", color="success"),
        # Placeholder for successful upload message + Spinner to symbolize loading
        dbc.Spinner(html.Div(id='output-uploader', className="mt-3"))], className="mt-3"),
        filename]


# Called when 'Upload to XNAT' button (appears after dash-uploader received an upload) is clicked
# and triggers the file upload to XNAT.
@callback(
    Output('output-uploader', 'children'),
    Input('click-upload', 'n_clicks'),
    State('project_name', 'value'),
    State('directory_name', 'value'),
    State('filename-storage', 'data'),
    State('upload_file_tags', 'value'),
)
def upload_tempfile_to_xnat(btn: int, project_name: str, dir_name: str, filename: str, tags: str):
    if ctx.triggered_id == "click-upload":
        if project_name:
            # Project name shall not contain whitespaces
            project_name = str(project_name).replace(" ", "_")
            try:
                with get_connection() as connection:
                    if dir_name and tags:
                        Project(connection, project_name).insert(
                            filename, dir_name, tags)
                    
                    elif tags:
                        # If the user entered no diretory name but tags
                        Project(connection, project_name).insert(
                            filename, tags)
                    elif dir_name:
                        # If the user entered a diretory name but no tags
                        Project(connection, project_name).insert(
                            filename, dir_name)
                    else:
                        # If the user entered no diretory name or tags
                        Project(connection, project_name).insert(filename)

                    # Remove tempdir after successful upload to XNAT
                    shutil.rmtree(dirpath)
                return dbc.Alert([f"The upload was successful! ",
                                  dcc.Link(f"Click here to go to {project_name}.",
                                           href=f"/project/{project_name}",
                                           className="fw-bold text-decoration-none",
                                           style={'color': colors['links']})], color="success")

            except Exception as err:
                # TODO: differentiate between different exceptions
                return dbc.Alert("Upload unsuccessful: " + str(err), color="danger")

        else:
            return dbc.Alert("Please specify Project Name.", color="danger")

    else:
        return no_update

#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None):
    return [html.H1(
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),
        uploader(project_name),
        # Store filename for upload to xnat https://dash.plotly.com/sharing-data-between-callbacks
        dcc.Store(id='filename-storage')
    ]
