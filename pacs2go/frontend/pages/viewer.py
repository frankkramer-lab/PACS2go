import base64
import io
import json
from pacs2go.data_interface.exceptions.exceptions import DownloadException
from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulGetException
from pacs2go.data_interface.pacs_data_interface import File
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection
from pacs2go.frontend.helpers import login_required_interface
from pacs2go.frontend.helpers import pil_to_b64
from tempfile import TemporaryDirectory
from typing import List
from typing import Optional

import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import pydicom
from dash import callback
from dash import ctx
from dash import dash_table
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import register_page
from dash import State
from flask_login import current_user
from PIL import Image
# from dash_slicer import VolumeSlicer
# from nilearn import image


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
            'records'), [{"name": i, "id": i} for i in df.columns])

    elif file.format == 'NIFTI':
        # TODO: implement dash-slicer --> check if dash version is compatible (CURRENT PROBLEM: graph is empty)
        # img = image.load_img(file.data)
        # mat = img.affine
        # img = img.get_data()
        # img = np.copy(np.moveaxis(img, -1, 0))[:, ::-1]
        # img = np.copy(np.rot90(img, 3, axes=(1, 2)))
        # spacing = abs(mat[2, 2]), abs(mat[1, 1]), abs(mat[0, 0])
        # slicer1 = VolumeSlicer(get_app(), volume=img,
        #                         axis=0, spacing=spacing)
        # content = html.Div([slicer1.graph, slicer1.slider, *slicer1.stores, html.H5(str())])
        content = dbc.Alert(
            "At this current version NIFTI files can not be displayed.", color="danger")

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
        ]))

    else:
        # Handle all other file formats that are at this point not displayable
        content = dbc.Alert(
            "File format currently not displayable.", color="danger")

    # Build dbc Card View that displays file information
    data = dbc.Card(
        dbc.CardBody(
            [
                html.H6([html.B("File Name: "), f"{file.name}"]),
                html.H6([html.B("File Format: "), f"{file.format}"]),
                html.H6([html.B("File Content Type: "),
                        f"{file.content_type}"]),
                html.H6([html.B("File Tags: "), f"{file.tags}"]),
                html.H6([html.B("File Size: "),
                         f"{round(file.size/1024,2)} KB ({file.size} Bytes)"]),
                html.Div([content]),
                html.Div([dbc.Button("Download File", id="btn_download"), dcc.Download(
                    id="download-file"), dcc.Store(data=file.name, id='file_name')], className="mt-3")
            ],))

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
        dbc.Row([
            # dbc.Col(dbc.Button(html.I(className="bi bi-arrow-left"), id="previous", class_name="align-text-end"),),
            dbc.Col(dbc.Spinner(html.Div(id="current_image"))),
            # dbc.Col(dbc.Button(html.I(className="bi bi-arrow-right"), id="next")),
        ])
    ], className="d-flex justify-content-center")


#################
#   Callbacks   #
#################


@callback(
    [Output('current_image', 'children')], 
    [Input('image-dropdown', 'value')],
    State('directory', 'data'),
    State('project', 'data'))
# Callback to show the contents of a selected file in the viewer
def show_chosen_file(chosen_file_name: str, directory_name: str, project_name: str):
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
                    dcc.Link(f"{directory_name.rsplit('-')[1]}", href=f"/dir/{project_name}/{directory_name}", style={"color": colors['sage'], "marginRight": "1%"}), 
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span("File Viewer", className='active fw-bold',style={"color": "#707070"})
                ],
                className='breadcrumb'
            ),

            dcc.Link(
                html.H1(f"Directory {directory_name.rsplit('-')[1]}"), href=f"/dir/{project_name}/{directory_name}",
                className="mb-3 fw-bold text-decoration-none", style={'color': colors['links']}),
            # Get Dropdown with file names
            files_dropdown(files, file_name),
            # Show file details of chosen file
            file_card_view(),
        ])

    else:
        return dbc.Alert("No Project or Directory specified.", color="danger")
