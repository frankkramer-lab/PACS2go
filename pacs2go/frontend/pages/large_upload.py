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
    FailedConnectionException, UnsuccessfulGetException,
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
            if p.your_user_role != 'Collaborators':
                project_list.append(p.name)

        return project_list

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return ["No database connection."]

def get_subdirectory_names_recursive(directory):
    # Recursively fetch all nested subdirectories using depth-first traversal
    dir_list = []
    for d in directory.get_subdirectories():
        label = f"{d.name.replace('::', ' / ')}"
        dir_list.append(html.Option(label=label, value=d.name))
        dir_list.extend(get_subdirectory_names_recursive(d))

    return dir_list

def get_directory_names(project: Project) -> List[str]:
    # Get List of all project names as html Options
    try:
        directories = get_connection().get_project(project).get_all_directories()
        dir_list = []

        for d in directories:
            # html option to create a html datalist
            dir_list.append(html.Option(label=d.name.replace('::', ' / '), value=d.name))
            if len(d.get_subdirectories()) > 0:
                dir_list.extend(get_subdirectory_names_recursive(d))
            
        return dir_list

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return ["No database connection."]


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
                 #html.Datalist(children=get_project_names(),id='project_names'),
                 dcc.Dropdown(options=get_project_names(),id="project_name", placeholder="Project Name...",
                          value=passed_project),
                 dbc.FormText(["Please choose a project. To create a new project go to", dcc.Link(' projects', href='/projects',style={"color":colors['sage']}), "."])], className="mb-3"),
            dbc.Col(
                [dbc.Label("Directory"),
                 html.Datalist(id='dir_names'),
                 dbc.Input(id="directory_name",
                           placeholder="Directory Name... (optional)", list='dir_names'),
                 dbc.FormText("If you choose not to specify the name of the directory, the current date and time will be used")], className="mb-3")
        ]),
        dbc.Row(dbc.Col(
                [dbc.Label("Tags - If you wish, you may add tags that describe your files' contents. Please separate each tag by comma."),
                 dbc.Input(id="upload_file_tags",
                           placeholder="File tags like \'Control group, Dermatology,...\' (optional)"),
                 dbc.FormText("Tags will be added to every file.")], className="mb-3")),
        dbc.Row(dbc.Col(
                [dbc.Label("Modality - In case that the modality is consistent for all files."),
                 dbc.Input(id="upload_file_modality",
                           placeholder="CT, MRI,... (optional)"),
                 dbc.FormText("Modality will be added to every file.")], className="mb-3")),
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
    State('upload_file_modality', 'value'), 
    prevent_initial_call=True
)
def upload_tempfile_to_xnat(btn: int, project_name: str, dir_name: str, filename: str, tags: str, modality: str):
    if ctx.triggered_id == "click-upload":
        if project_name:
            # Project name shall not contain whitespaces
            project_name = str(project_name).replace(" ", "_")
            try:
                connection = get_connection()
                project = connection.get_project(project_name)
                if project.your_user_role == 'Collaborators':
                    return dbc.Alert("Upload not possible! Your user role in the project '" + project.name + "' does not allow you to upload files.", color="danger")

                tags = tags if tags else ''
                modality = modality if modality else '-'
                if dir_name:
                    new_location = project.insert(filename, dir_name, tags, modality)
                else:
                    # If the user entered no diretory name
                    new_location = project.insert(file_path=filename, tags_string=tags, modality=modality)

                if filename.endswith('.zip'):
                    dir_name = new_location.name
                else:
                    dir_name = new_location.directory.name

                # Remove tempdir after successful upload to XNAT
                shutil.rmtree(dirpath)
                return dbc.Alert(["The upload was successful! ",
                                  dcc.Link(f"Click here to go to the directory {dir_name.rsplit('::', 1)[-1]}.",
                                           href=f"/dir/{project_name}/{dir_name}",
                                           className="fw-bold text-decoration-none",
                                           style={'color': colors['links']})], color="success")

            except (FailedConnectionException, UnsuccessfulGetException, WrongUploadFormatException, UnsuccessfulUploadException) as err:
                return dbc.Alert(str(err), color="danger")

        else:
            return dbc.Alert("Please specify Project Name.", color="danger")

    else:
        return no_update

@callback(Output('dir_names', 'children'),Input('project_name','value'), prevent_initial_call=True)
def display_directory_dropdown(project):
    # When a project is selected, the directory field suggests existing directories to upload to
    return get_directory_names(project)

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
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),

        uploader(project_name),
        
        # Store filename for upload to xnat https://dash.plotly.com/sharing-data-between-callbacks
        dcc.Store(id='filename-storage')
    ]
