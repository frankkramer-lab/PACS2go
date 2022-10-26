import tempfile
import shutil
from typing import List
from PIL import Image
from dash import register_page, html, dcc, get_app, callback, ctx, no_update
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import get_connection, colors
import dash_uploader as du  # https://github.com/np-8/dash-uploader
import uuid


register_page(__name__, title='PACS2go 2.0',
              path_template='/upload/<project_name>')

# setup dash-uploader
# attention: global variables not recommended for multi-user environments
dirpath = tempfile.mkdtemp()
UPLOAD_FOLDER_ROOT = dirpath
du.configure_upload(get_app(), UPLOAD_FOLDER_ROOT)

def get_project_names() -> List[str]:
    with get_connection() as connection:
        project_list = []
        for p in connection.get_all_projects():
            project_list.append(html.Option(value=p.name))
        return project_list

def get_upload_component(id):
    # dash-uploader Upload component
    return du.Upload(
        id=id,
        max_file_size=1024,  # 1GB
        filetypes=['zip', 'jpeg', 'jpg', 'dcm', 'json', 'nii'],
        upload_id=uuid.uuid1(),  # Unique session id
        text='Drag and Drop your file right here! Or click here to select a file!',
        text_completed='Ready for XNAT Upload: ',
    )


def uploader(passed_project: str):
    # if user navigates directly to upload, project name input field will be empty
    if passed_project == 'none':
        passed_project = ''
    # Upload drag and drop area
    return html.Div([
        dbc.Row(html.H5([html.B("1."), " Specify the project's name."])),
        dbc.Row([
            dbc.Col(
                # input field value equals project name, if user navigates to upload via a specific project
                [dbc.Label("Project"),
                 html.Datalist(children=get_project_names(), id='project_names'),
                 dbc.Input(id="project_name", type="text", placeholder="Project Name...", required=True, value=passed_project, list='project_names'),
                 dbc.FormText("If you choose a pre-existent project name, the data will be inserted into this project. Otherwise a new project will be created.")], className="mb-3"),
            dbc.Col(
                [dbc.Label("Directory"),
                 dbc.Input(id="directory_name",
                           placeholder="Directory Name (optional)"),
                 dbc.FormText("If you choose not to specify the name of the directory, the current date and time will be used")], className="mb-3")
        ]),
        dbc.Row(html.H5([html.B("2."), ' Please select a zip folder or a single file to upload.', html.Br(),
                         'Accepted formats include DICOM, NIFTI, JPEG and JSON.'])),
        dbc.Row(
            [
                get_upload_component(id='dash-uploader'),
                # placeholder for 'Upload to XNAT' button
                html.Div(id='du-callback-output'),
            ])
    ])


#################
#   Callbacks   #
#################

# callback for the dash-uploader Upload component -> called when something is uploaded
# triggers the appearance of an 'Upload to XNAT' button
@du.callback(
    output=[Output('du-callback-output', 'children'),
            Output('filename-storage', 'data')],
    id='dash-uploader',
)
def pass_filename_and_show_upload_button(filenames):
    # get file -> only one file should be in this list bc 'dirpath' is removed after each upload
    filename = filenames[0]
    return [html.Div([
        html.H5([html.B("3."), ' Confirm upload to XNAT.']),
        dbc.Button("Upload to XNAT", id="click-upload",
                   size="lg", color="success"),
        # placeholder for successful upload message
        dbc.Spinner(html.Div(id='output-uploader', className="mt-3"))], className="mt-3"),
        filename]


# called when 'Upload to XNAT' button (appears after dash-uploader received an upload) is clicked
# and triggers the file upload to XNAT
@callback(
    Output('output-uploader', 'children'),
    Input('click-upload', 'n_clicks'),
    State('project_name', 'value'),
    State('directory_name', 'value'),
    State('filename-storage', 'data')
)
def upload_tempfile_to_xnat(btn, project_name, dir_name, filename):
    if ctx.triggered_id == "click-upload":
        if project_name:
            # project name shall not contain whitespaces
            project_name = str(project_name).replace(" ", "_")
            try:
                with get_connection() as connection:
                    if dir_name:
                        Project(connection, project_name).insert(
                            filename, dir_name)
                    else:
                        # if dir_name is an empty string
                        Project(connection, project_name).insert(filename)
                    # remove tempdir after successful upload to XNAT
                    shutil.rmtree(dirpath)
                return dbc.Alert([f"The upload was successful! ", dcc.Link(f"Click here to go to {project_name}.",
                                                                         href=f"/project/{project_name}", className="fw-bold text-decoration-none", style={'color': colors['links']})], color="success")
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


def layout(project_name=None):
    return [html.H1(
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),
        uploader(project_name),
        # store filename for upload to xnat https://dash.plotly.com/sharing-data-between-callbacks
        dcc.Store(id='filename-storage')
    ]
