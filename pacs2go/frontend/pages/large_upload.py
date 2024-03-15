import shutil
import tempfile
import uuid
from typing import List, Optional

import dash_bootstrap_components as dbc
import dash_uploader as du  # https://github.com/np-8/dash-uploader
from dash import callback, ctx, dcc, get_app, html, no_update, register_page
from dash.dependencies import Input, Output, State
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulCreationException, UnsuccessfulGetException,
    UnsuccessfulUploadException, WrongUploadFormatException)
from pacs2go.data_interface.pacs_data_interface.project import Project
from pacs2go.frontend.helpers import (colors, get_connection,
                                      login_required_interface)

register_page(__name__, title='Upload - PACS2go',
              path_template='/upload/<project_name>')

# Setup dash-uploader
dirpath = tempfile.mkdtemp()
UPLOAD_FOLDER_ROOT = dirpath # still stateless because du uses upload id's -> multiuser friendly
du.configure_upload(get_app(), UPLOAD_FOLDER_ROOT)


def get_project_names() -> List[str]:
    # Get List of all project names as html Options
    try:
        connection = get_connection()
        project_list = []

        for p in connection.get_all_projects():
            if p.your_user_role in ['Owners', 'Members']:
                project_list.append(p.name)

        return project_list

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return ["No database connection."]

def get_subdirectory_names_recursive(directory):
    # Recursively fetch all nested subdirectories using depth-first traversal
    dir_list = []
    for d in directory.get_subdirectories():
        dir_list.append({'label': d.unique_name.replace('::', ' / '), 'value':d.unique_name})
        dir_list.extend(get_subdirectory_names_recursive(d))

    return dir_list

def get_directory_names(project: Project) -> List[str]:
    # Get List of all project names as html Options
    try:
        directories = get_connection().get_project(project).get_all_directories()
        dir_list = []

        for d in directories:
            # html option to create a html datalist
            dir_list.append({'label': d.unique_name.replace('::', ' / '), 'value':d.unique_name})
            if len(d.get_subdirectories()) > 0:
                dir_list.extend(get_subdirectory_names_recursive(d))
            
        return dir_list

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return ["No database connection."]


def get_upload_component(id: str):
    # dash-uploader Upload component
    return du.Upload(
        id=id,
        max_file_size=51200,  # 50GB
        filetypes=['zip', 'jpeg', 'jpg', 'dcm',
                   'json', 'nii', 'png', 'tiff', 
                   'csv', 'gz', 'pdf', 'json',
                   'md', 'py', 'ipynb', 'gif',
                   'svg'],
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
        dbc.Card(dbc.CardBody([       dbc.Row(html.H5([html.B("1. Specify the project's name and metadata")])),
            dbc.Row([
                dbc.Col(
                    # Input field value equals project name, if user navigates to upload via a specific project
                    [dbc.Label(html.B("Project")),
                    #html.Datalist(children=get_project_names(),id='project_names'),
                    dcc.Dropdown(options=get_project_names(),id="project_name", placeholder="Project Name...",
                            value=passed_project),
                    dbc.FormText(["Please choose a project. To create a new project go to", dcc.Link(' projects', href='/projects',style={"color":colors['sage']}), "."])], className="mb-3"),
                dbc.Col(
                    [dbc.Label(html.B("Directory"),),
                    dcc.Dropdown(options=[],id="directory_name", placeholder="Directory Name... (optional)",
                            value=None),
                    dbc.FormText("Select a directory from the dropdown if desired. For single file uploads, a new directory with the current timestamp will be created if none is selected.")], className="mb-3")
            ]),
            dbc.Row(dbc.Col(
                    [dbc.Label([html.B("Tags")," - If you wish, you may add tags that describe your files' contents. Please separate each tag by comma."]),
                    dbc.Input(id="upload_file_tags",
                            placeholder="File tags like \'Control group, Dermatology,...\' (optional)"),
                    dbc.FormText("Tags will be added to every file.")], className="mb-3")),
            dbc.Row(dbc.Col(
                    [dbc.Label([html.B("Modality")," - In case that the modality is consistent for all files."]),
                    dbc.Input(id="upload_file_modality",
                            placeholder="CT, MRI,... (optional)"),
                    dbc.FormText("Modality will be added to every file.")], className="mb-3")),
            dbc.Row(dbc.Col(
                    [dbc.Label([html.B("Unpacking a zip file")," - "]),
                     dbc.Checklist(
                        options=[
                            {"label": "Unpack zip file directly to chosen directory", "value": 1},
                        ],
                        value= [],
                        id="upload_file_unpack_zip",
                        switch=True,
                    ),
                    dbc.FormText("If not activated, a new directory will be created for the top level folder of the zip aka the actual zipped folder inside the chosen directory. \
                                 For each sub-folder inside this folder a directory will be created either way. Choosing a directory is mandatory for this option, else this option is ignored.")], className="mb-3")),
            ]), className="custom-card mb-3"),

        dbc.Card(dbc.CardBody([
            dbc.Row(html.H5([html.B("2. Please select a zip folder or a single file to upload."), html.Br(),
                         'Accepted formats include DICOM, NIFTI, JPEG, PNG, TIFF, CSV, TXT, JSON and many more.', html.Br(), html.Br(), 'Please make sure that all files have a valid file extension.'])),
            dbc.Row(
                [
                    get_upload_component(id='dash-uploader'),
            ], className="p-3")
        ],), className="custom-card mb-3"),
        # Placeholder for 'Upload to XNAT' button
        html.Div(id='du-callback-output'),
        dbc.Card(dbc.CardBody([
                html.Div([
                html.H5([html.B("3. Finish Upload and Assemble Metadata")]),
                dbc.Button("Complete Upload Process", id="click-upload",
                        size="lg", color="success", disabled=True),
                # Placeholder for successful upload message + Spinner to symbolize loading
                dcc.Loading(html.Div(id='output-uploader', className="mt-3"), color=colors['sage'], className="pb-5")])]
        ), className="custom-card mb-3")
    ])


#################
#   Callbacks   #
#################

# Callback for the dash-uploader Upload component -> called when something is uploaded
# Triggers the appearance of an 'Upload to XNAT' button
@du.callback(
    output=[Output('click-upload', 'disabled'),
            Output('filename-storage', 'data')],
    id='dash-uploader',
)
def pass_filename_and_show_upload_button(filenames: List[str]):
    # Get file -> only one file should be in this list bc 'dirpath' is removed after each upload
    filename = filenames[0]
    return False, filename

# Called when step 3 button (appears after dash-uploader received an upload) is clicked
# and triggers the file upload to XNAT.
@callback(
    Output('output-uploader', 'children'),
    Input('click-upload', 'n_clicks'),
    State('project_name', 'value'),
    State('directory_name', 'value'),
    State('filename-storage', 'data'),
    State('upload_file_tags', 'value'), 
    State('upload_file_modality', 'value'), 
    State('upload_file_unpack_zip', 'value'),
    prevent_initial_call=True
)
def upload_tempfile_to_xnat(btn: int, project_name: str, dir_name: str, filename: str, tags: str, modality: str, unpack:int):
    if ctx.triggered_id == "click-upload":
        if project_name:
            # Project name shall not contain whitespaces
            project_name = str(project_name).replace(" ", "_")

            if len(unpack) == 0:
                unpack = False
            else:
                unpack = True

            try:
                connection = get_connection()
                project = connection.get_project(project_name)
                if project.your_user_role == 'Collaborators':
                    return dbc.Alert("Upload not possible! Your user role in the project '" + project.name + "' does not allow you to upload files.", color="danger")

                tags = tags if tags else ''
                modality = modality if modality else '-'
                if dir_name:
                    new_location = project.insert(filename, dir_name, tags, modality, unpack)
                else:
                    # If the user entered no diretory name
                    new_location = project.insert(file_path=filename, tags_string=tags, modality=modality, unpack_directly=unpack)

                if filename.endswith('.zip'):
                    dir_name = new_location.unique_name
                else:
                    dir_name = new_location.directory.unique_name

                # Remove tempdir after successful upload to XNAT
                shutil.rmtree(dirpath)
                return dbc.Alert(["The upload was successful! ",
                                  dcc.Link(f"Click here to go to the directory {dir_name.rsplit('::', 1)[-1]}.",
                                           href=f"/dir/{project_name}/{dir_name}",
                                           className="fw-bold text-decoration-none",
                                           style={'color': colors['links']})], color="success")

            except (FailedConnectionException, UnsuccessfulGetException, WrongUploadFormatException, UnsuccessfulUploadException, Exception) as err:
                return dbc.Alert(str(err), color="danger")

        else:
            return dbc.Alert("Please specify Project Name.", color="danger")

    else:
        return no_update

@callback(Output('directory_name', 'options'),Input('project_name','value'), prevent_initial_call=True)
def display_directory_dropdown(project):
    # When a project is selected, the directory field suggests existing directories to upload to
    if project and project!='None':
        return get_directory_names(project)

# Define the callback function
@callback(
    Output('keep_alive_output', 'children'),  # Dummy output
    [Input('keep_alive_interval', 'n_intervals')],
    prevent_initial_callback=True
)
def keep_session_alive(n):
    try:
        # Heartbeat to keep session alive during upload
        get_connection()._file_store_connection.heartbeat()
    
        # We don't want to update any component
        return no_update
    except Exception:
        return dbc.Alert("Your session has expired, please try again.", color="danger")


#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None):
    if not current_user.is_authenticated:
        return login_required_interface()

    return [
        # Breadcrumbs
        html.Div(
        [
            dcc.Link("Home", href="/", style={"color": colors['sage'], "marginRight": "1%"}),
            html.Span(" > ", style={"marginRight": "1%"}),
            html.Span("Upload", className='active fw-bold',style={"color": "#707070"})],
            className='breadcrumb'),

        html.H1(
        children='PACS2go - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),

        uploader(project_name),
        
        dcc.Interval(
            id='keep_alive_interval',
            interval=2*60*1000,  # in milliseconds, 2 minutes * 60 seconds * 1000 ms
            n_intervals=0
        ),
        html.Div(id='keep_alive_output'),
        
        # Store filename for upload to xnat https://dash.plotly.com/sharing-data-between-callbacks
        dcc.Store(id='filename-storage')
    ]
