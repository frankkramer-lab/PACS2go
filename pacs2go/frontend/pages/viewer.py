import json
from typing import List
from typing import Optional

import dash_bootstrap_components as dbc
import numpy as np
from dash import callback
from dash import dcc
from dash import get_app
from dash import html
from dash import Input
from dash import Output
from dash import register_page
from dash import State
# from dash_slicer import VolumeSlicer
# from nilearn import image
from PIL import Image

from pacs2go.data_interface.pacs_data_interface import File
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection
from pacs2go.frontend.helpers import pil_to_b64


register_page(__name__, title='Viewer - PACS2go',
              path_template='/viewer/<project_name>/<directory_name>/<file_name>')


def get_file_list(project_name: str, directory_name: str) -> List[File]:
    with get_connection() as connection:
        # Get current project (passed through url/path)
        project = connection.get_project(project_name)

        if project:
            directory = project.get_directory(directory_name)
            # Return list of all the files in the directory
            return directory.get_all_files()

        else:
            raise Exception("No project found.")


def show_file(file: File):
    if file.format == 'JPEG':
        # Display JPEG contents as html Img
        content = html.Img(id="my-img", className="image",
                           src="data:image/png;base64, " + pil_to_b64(Image.open(file.data)))

    elif file.format == 'JSON':
        # Display contents of a JSON file as string
        f = open(file.data)
        content = json.dumps(json.load(f))

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
        #content = html.Div([slicer1.graph, slicer1.slider, *slicer1.stores, html.H5(str())])
        content = dbc.Alert(
            "At this current version NIFTI files can not be displayed.", color="danger")

    elif file.format == 'DICOM':
        # Display of DICOM files is currently not implemented
        content = dbc.Alert(
            "At this current version DICOM files can not be displayed.", color="danger")

    else:
        # Handle all other file formats that are at this point not displayable
        content = dbc.Alert(
            "File format currently not displayable.", color="danger")

    # Build dbc Card View that displays file information
    data = dbc.Card(
        dbc.CardBody(
            [
                html.H6(f"File Name: {file.name}"),
                html.H6(f"File Format: {file.format}"),
                html.H6(
                    f"File Size: {round(file.size/1024,2)} KB ({file.size} Bytes)"),
                html.Div([content]),
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


@callback([Output('current_image', 'children')], [Input('image-dropdown', 'value')],
          State('directory', 'data'), State('project', 'data'))
def show_chosen_file(chosen_file_name: str, directory_name: str, project_name: str):
    with get_connection() as connection:
        project = connection.get_project(project_name)

        if project:
            # get File object of the file that was chosen in the dropdown
            directory = project.get_directory(directory_name)
            file = directory.get_file(chosen_file_name)
            return [show_file(file)]


#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None, directory_name:  Optional[str] = None, file_name:  Optional[str] = None):
    try:
        if directory_name and project_name and file_name:
            # get list of files
            files = get_file_list(project_name, directory_name)
            return html.Div([
                # dcc Store components for project and directory name strings
                dcc.Store(id='directory', data=directory_name),
                dcc.Store(id='project', data=project_name),
                dcc.Link(
                    html.H1(f"Directory {directory_name}"), href=f"/dir/{project_name}/{directory_name}", 
                    className="mb-3 fw-bold text-decoration-none", style={'color': colors['links']}),
                # Get Dropdown with file names
                files_dropdown(files, file_name),
                # Show file details of chosen file
                file_card_view(),
            ])

        else:
            return dbc.Alert("No Project or Directory specified.", color="danger")

    except Exception as err:
        return dbc.Alert("No Directory found " + str(err), color="danger")
