import base64
import gzip
import io
import json
from tempfile import TemporaryDirectory
from typing import List, Optional

import dash_bootstrap_components as dbc
import nibabel
import numpy as np
import pandas as pd
import plotly.express as px
import pydicom
from dash import (Input, Output, State, callback, ctx, dash_table, dcc, html,
                  no_update, register_page)
from dash.exceptions import PreventUpdate
from flask_login import current_user
from PIL import Image

from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException,
    UnsuccessfulAttributeUpdateException, UnsuccessfulDeletionException,
    UnsuccessfulGetException)
from pacs2go.data_interface.pacs_data_interface.file import File
from pacs2go.frontend.helpers import (colors, get_connection,
                                      login_required_interface, pil_to_b64)


register_page(__name__, title='Viewer - PACS2go',
              path_template='/viewer/<project_name>/<directory_name>/<file_name>')


def get_file_list(project_name: str, directory_name: str) -> List[File]:
    try:
        connection = get_connection()
        # Get current project (passed through url/path)
        directory = connection.get_directory(project_name, directory_name)
        # Return list of all the files in the directory
        return directory.get_all_files()

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return dbc.Alert(str(err), color="danger")


def show_file(file: File):
    if file == None:
        return dbc.Alert("No choosen file.", color='warning')
    if file.format == 'JPEG' or file.format == 'PNG' or file.format == 'TIFF':
        # Display JPEG contents as html Img
        encoded_image = base64.b64encode(file.data).decode("utf-8")
        content = html.Img(id="my-img", className="image", width="100%",
                        src=f"data:image/png;base64,{encoded_image}")

    elif file.format == 'JSON':
        # Display contents of a JSON file
        json_str = file.data.decode("utf-8")
        json_data = json.loads(json_str)
        content = html.Pre(json.dumps(json_data, indent=2))

    elif file.format == 'CSV':
        # Display CSV as data table
        csv_str = file.data.decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_str))
        content = dash_table.DataTable(df.to_dict(
            'records'), [{"name": i, "id": i} for i in df.columns], 
                                       style_table={'overflowY': 'scroll'})
        
    elif file.format == 'Markdown':
        markdown_text = file.data.decode('utf-8')
        content = dcc.Markdown(markdown_text)

    elif file.format == 'NIFTI' or file.format == 'compressed (NIFTI)':
        if file.name.endswith('.nii'):
            nifti = nibabel.Nifti1Image.from_bytes(file.data)
            # Get the data array
            volume_data = nifti.get_fdata()
        
        if file.name.endswith('.nii.gz'):
            nifti_gz_bytes_io = gzip.decompress(file.data) 
            nifti = nibabel.Nifti1Image.from_bytes(nifti_gz_bytes_io)
            volume_data = nifti.get_fdata()
        
        content = html.Div([
            dcc.Graph(id='nifti-slice-viewer',style={'height': '80vw'}),
            dcc.Slider(
                id='slice-slider',
                min=0,
                max=volume_data.shape[2] - 1,
                value=volume_data.shape[2] // 2,
                tooltip={"always_visible": True},
                step=1,
            )
        ])

    elif file.format == 'DICOM':
        # Display of DICOM file
        dcm = pydicom.dcmread(io.BytesIO(file.data))
        new_image = dcm.pixel_array.astype(
            float)  # Convert the values into float

        # White-Black leveling
        image_correct_bw = (np.maximum(new_image, 0) / new_image.max()) * 255.0

        # Convert to PIL
        image_correct_bw = np.uint8(image_correct_bw)
        final_image = Image.fromarray(image_correct_bw)

        content = dbc.Card(dbc.CardBody([
            html.H3("DICOM Information"),
            html.H5(f"Patient Name: {dcm.PatientName}"),
            html.H5(f"Study Date: {dcm.StudyDate}"),
            html.H5(f"Study Description: {dcm.StudyDescription}"),
            # ... (add any other relevant information that you want to display)
            html.Img(id="my-img", className="image", width="100%",
                    src='data:image/png;base64,{}'.format(pil_to_b64(final_image)))
        ], className="custom-card"))

    else:
        # Handle all other file formats that are at this point not displayable
        content = dbc.Alert(
            "File format currently not displayable.", color="danger")

    # Build dbc Card View that displays file information
    data = dbc.Card(
        dbc.CardBody(
            [
                html.H6([html.B("File Name: "), f"{file.name}"]),
                html.H6([html.B("Format: "), f"{file.format}"]),
                html.H6([html.B("Modality: "), f"{file.modality}"]), 
                html.H6([html.B("File Content Type: "),
                        f"{file.content_type}"]),
                html.H6([html.B("Tags: "), f"{file.tags}"]),
                html.H6([html.B("File Size: "),
                         f"{round(file.size/1024,2)} KB ({file.size} Bytes)"]),
                html.H6([html.B("Uploaded on: "), f"{file.timestamp_creation.strftime('%d.%m.%Y, %H:%M:%S')}"]), 
                html.H6([html.B("Last updated on: "), f"{file.last_updated.strftime('%d.%m.%Y, %H:%M:%S')}"]), 
                html.Div([dcc.Loading(content, color=colors['sage'])]),
                html.Div([dbc.Button("Download File", id="btn_download", outline=True, color="success"), 
                          dcc.Download(id="download-file"), 
                          dcc.Store(data=file.name, id='file_name'), 
                          modal_edit_file(file), modal_delete_file(file)], className="mt-3 d-grid gap-2 d-md-flex justify-content-md-end")
            ], className="custom-card"))

    return data


def files_dropdown(files: List[File],  file_name: Optional[str] = None):
    if file_name:
        # When a file_name is given select it in the dropdown
        first_file = file_name

    else:
        # Otherwise show first file in directory
        first_file = files[0].name

    return html.Div([html.H4("Choose a file: "),
                     dcc.Dropdown(id='image-dropdown',
                                  options=[{'label': f.name, 'value': f.name}
                                           for f in files],
                                  value=first_file, className="mb-3")])


def file_card_view():
    return html.Div([
            dbc.Col(html.Div(id="current_image")),
    ])


def modal_delete_file(file: File):
    if file.directory.project.your_user_role == 'Owners':
        # Modal view for directory deletion
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-trash")],id='delete_file_viewer' , size="md", color="danger"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Delete File")),
                    dbc.ModalBody([
                        html.Div("Are you sure you want to delete this file?",
                            id='delete_file_viewer_content'),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the deletion of the file
                        dbc.Button("Delete File",'delete_file_and_close_viewer', color="danger"),
                        # Button which causes modal to close/disappear
                        dbc.Button(
                            "Close", id='close_modal_delete_file_viewer', outline=True, color="success"),
                    ]),
                ],
                id='modal_delete_file_viewer',
                is_open=False,
            ),
        ])



def modal_edit_file(file:File):
    # Modal view for project creation
    if file.directory.project.your_user_role == 'Owners' or file.directory.project.your_user_role == 'Members':
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-pencil")], id="edit_file_metadata", size="md", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(f"Edit {file.name}")),
                    dbc.ModalBody([
                        html.Div(id='edit_file_metadata_content'),
                        dbc.Label(
                            "Please enter desired modality.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Input(id="edit_file_modality",
                                placeholder="e.g.: CT, MRI", value=file.modality),
                        dbc.Label(
                            "Please enter desired tags.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Input(id="edit_file_tags",
                                placeholder="e.g.: Dermatology, control group", value=file.tags),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Update Directory Metadata",
                                id="edit_file_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_edit_file", outline=True, color="success")
                    ]),
                ],
                id="modal_edit_file_metadata",
                is_open=False,
            ),
        ])


#################
#   Callbacks   #
#################
@callback(
    [Output('modal_edit_file_metadata', 'is_open'),
     Output('edit_file_metadata_content', 'children'),
     Output('current_image', 'children', allow_duplicate=True)],
    [Input('edit_file_metadata', 'n_clicks'),
     Input('close_modal_edit_file', 'n_clicks'),
     Input('edit_file_and_close', 'n_clicks')],
    State("modal_edit_file_metadata", "is_open"),
    State('project', 'data'),
    State('directory', 'data'),
    State('file_name', 'data'),
    State('edit_file_modality', 'value'),
    State('edit_file_tags', 'value'),
    prevent_initial_call=True)
# Callback used to edit project description, parameters and keywords
def modal_edit_file_callback(open, close, edit_and_close, is_open, project_name, directory_name, file_name, modality, tags):
    # Open/close modal via button click
    if (ctx.triggered_id == "edit_file_metadata" or ctx.triggered_id == "close_modal_edit_file") and open != None:
        return not is_open, no_update, no_update

    # User does everything "right"
    elif ctx.triggered_id == "edit_file_and_close":
        try:
            connection = get_connection()
            file = connection.get_file(project_name, directory_name, file_name)
            if modality:
                file.set_modality(modality)
            if tags:
                file.set_tags(tags)
            # Retrieve updated file to forece reload
            file = connection.get_file(project_name, directory_name, file_name)
            return not is_open, no_update, show_file(file)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate
    

@callback(
    [Output('modal_delete_file_viewer', 'is_open'),
     Output('delete_file_viewer_content', 'children'),Output('current_image', 'children', allow_duplicate=True)],
    [Input('delete_file_viewer', 'n_clicks'),
     Input('close_modal_delete_file_viewer', 'n_clicks'),
     Input('delete_file_and_close_viewer', 'n_clicks')],
    [State('modal_delete_file_viewer', 'is_open'),
     State('directory', 'data'),
     State('project', 'data'),
     State('file_name', 'data')],
    prevent_initial_call=True
)
# Callback for the file deletion modal view and the actual file deletion
def modal_and_file_deletion(open, close, delete_and_close, is_open, directory_name, project_name, file_name):
    # Delete Button in File list - open/close Modal View
    if (ctx.triggered_id == "delete_file_viewer" or ctx.triggered_id == "close_modal_delete_file_viewer") and open != None:
        return not is_open, no_update, no_update
    
    # Delete Button in the Modal View
    elif ctx.triggered_id == 'delete_file_and_close_viewer':
        try:
            connection = get_connection()
            file = connection.get_file(
                project_name, directory_name, file_name)
            # Delete File
            file.delete_file()
            # Close Modal and show message
            return is_open, dbc.Alert(
                [f"The file {file_name} has been successfully deleted! "], color="success"), show_file(None)
        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
            return not is_open, dbc.Alert(str(err), color="danger"), no_update
            
    else:
        raise PreventUpdate
    

@callback(
    [Output('current_image', 'children')], 
    [Input('image-dropdown', 'value')],
    State('directory', 'data'),
    State('project', 'data'))
# Callback to show the contents of a selected file in the viewer
def show_chosen_file(chosen_file_name: str, directory_name: str, project_name: str):
    if chosen_file_name == 'none':
        return [dbc.Alert("No choosen file.", color='warning')]
    try:
        connection = get_connection()
        # Get file
        file = connection.get_file(
            project_name, directory_name, chosen_file_name)
        # Return visualization of file details if file exists
        return [show_file(file)]
    except (FailedConnectionException, UnsuccessfulGetException) as err:
        # Show nothing if file does not exist.
        return [dbc.Alert(str(err), color='warning')]
    

@callback(
    Output('nifti-slice-viewer', 'figure'),
    [Input('slice-slider', 'value')],
    State('image-dropdown', 'value'),
    State('directory', 'data'),
    State('project', 'data')
)
def update_nifti_figure(selected_slice, chosen_file_name: str, directory_name: str, project_name: str):
    try:
        connection = get_connection()
        # Get file
        file = connection.get_file(
            project_name, directory_name, chosen_file_name)
        if file.format in ['NIFTI', 'compressed (NIFTI)']:
            
            if file.name.endswith('nii'):
                nifti = nibabel.Nifti1Image.from_bytes(file.data)
                # Get the data array
                volume_data = nifti.get_fdata()
            elif file.name.endswith('.nii.gz'):
                nifti_gz_bytes_io = gzip.decompress(file.data) 
                nifti = nibabel.Nifti1Image.from_bytes(nifti_gz_bytes_io)
                volume_data = nifti.get_fdata()

            # Extract the selected slice
            slice_data = volume_data[:, :, selected_slice]
            # Create figure using Plotly Express
            fig = px.imshow(np.fliplr(slice_data.T), color_continuous_scale='gray', origin='lower')
            fig.update_layout(coloraxis_showscale=False)
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)
            return fig

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        # Show nothing if file does not exist.
        return [dbc.Alert(str(err), color='warning')]
    


@callback(
    Output("download-file", "data"),
    Input("btn_download", "n_clicks"), 
    State("file_name", "data"), 
    State('directory', 'data'), 
    State('project', 'data'),
    prevent_initial_call=True,
)
# Callback to download the selected file
def download_file(n_clicks, file_name, dir, project):
    if ctx.triggered_id == 'btn_download':
        with TemporaryDirectory() as tempdir:
            try:
                connection = get_connection()
                file = connection.get_file(project, dir, file_name)
                temp_dest = file.download(destination=tempdir)
                return dcc.send_file(temp_dest)
            
            except (FailedConnectionException, UnsuccessfulGetException, DownloadException) as err:
                dbc.Alert(str(err), color='warning')


#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None, directory_name:  Optional[str] = None, file_name:  Optional[str] = None):
    if not current_user.is_authenticated:
        return login_required_interface()

    if directory_name and project_name and file_name:
        try:
            # Get list of files
            files = get_file_list(project_name, directory_name)

        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")

        if directory_name.count('::') >= 1:
            breadcrumb_buffer = html.Span(" ...   \u00A0 >  ", style={"marginRight": "1%"})
        else:
            breadcrumb_buffer = None
        
        return html.Div([
            # dcc Store components for project and directory name strings
            dcc.Store(id='directory', data=directory_name),
            dcc.Store(id='project', data=project_name),

            # Breadcrumbs                         
            html.Div(
                [
                    dcc.Link("Home", href="/", style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    dcc.Link("All Projects", href="/projects", style={"color": colors['sage'], "marginRight": "1%"}), 
                    html.Span(" > ", style={"marginRight": "1%"}),
                    dcc.Link(f"{project_name}", href=f"/project/{project_name}", style={"color": colors['sage'], "marginRight": "1%"}), 
                    html.Span(" > ", style={"marginRight": "1%"}),
                    breadcrumb_buffer,
                    dcc.Link(f"{directory_name.rsplit('::', 1)[-1]}", href=f"/dir/{project_name}/{directory_name}", style={"color": colors['sage'], "marginRight": "1%"}), 
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span("File Viewer", className='active fw-bold',style={"color": "#707070"})
                ],
                className='breadcrumb'
            ),

            dcc.Link(
                html.H1(f"Directory {directory_name.rsplit('::', 1)[-1]}"), href=f"/dir/{project_name}/{directory_name}",
                className="mb-3 fw-bold text-decoration-none", style={'color': colors['links']}),
            # Get Dropdown with file names
            files_dropdown(files, file_name),
            # Show file details of chosen file
            file_card_view(),
        ])

    else:
        return dbc.Alert("No Project or Directory specified.", color="danger")
