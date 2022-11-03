from typing import List
from dash import html, callback, Input, Output, register_page, ctx, State, no_update, dcc
from pacs2go.data_interface.pacs_data_interface import Directory, File
import dash_bootstrap_components as dbc
from pacs2go.frontend.helpers import get_connection, colors, pil_to_b64
from PIL import Image

register_page(__name__, title='Viewer - PACS2go',
              path_template='/viewer/<project_name>/<directory_name>')


def get_file_array(project_name: str, directory_name: str):
    with get_connection() as connection:
        project = connection.get_project(project_name)
        directory = project.get_directory(directory_name)
        return directory.get_all_files()


def show_image(file: File):
    if file.format == 'JPEG':
        image = html.Img(id="my-img", className="image",
                         src="data:image/png;base64, " + pil_to_b64(Image.open(file.data)))
        data = dbc.Card(
            dbc.CardBody(
                [
                    html.H6(f"File Name: {file.name}"),
                    html.H6(f"File Format: {file.format}"),
                    html.H6(f"File Size: {file.size}"),
                    html.Div([image]),
                ],))
        return data
    else:
        return html.Div()


def files_dropdown(files: List[File]):
    return html.Div([html.H4("Choose a file: "),
                     dcc.Dropdown(id='image-dropdown',
                                  options=[{'label': f.name, 'value': f.name}
                                           for f in files],
                                  value=files[0].name, className="mb-3")])


def slide_show():
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
def show_chosen_image(file_name: str, directory_name: str, project_name: str):
    with get_connection() as connection:
        directory = connection.get_project(
            project_name).get_directory(directory_name)
        file = directory.get_file(file_name)
        return [show_image(file)]

#################
#  Page Layout  #
#################


def layout(project_name: str = None, directory_name: str = None):
    try:
        files = get_file_array(project_name, directory_name)
    except:
        return dbc.Alert("No Directory found", color="danger")
    return html.Div([
        dcc.Store(id='directory', data=directory_name),
        dcc.Store(id='project', data=project_name),
        dcc.Store(id='files'),
        dbc.Row([
                dbc.Col(html.H1(f"Directory {directory_name}", style={
                    'textAlign': 'left', })),
                ], className="mb-3"),
        files_dropdown(files),
        slide_show(),
    ])
