from dash import html, callback, Input, Output, register_page, ctx, State, no_update, dcc
from pacs2go.data_interface.pacs_data_interface import Directory, File
import dash_bootstrap_components as dbc
from pacs2go.frontend.helpers import get_connection, colors, pil_to_b64
from PIL import Image

register_page(__name__, title='Viewer - PACS2go',
              path_template='/viewer/<project_name>/<directory_name>')



def show_image(file: File):
    if file.format == 'JPEG':
        image = html.Img(id="my-img", className="image", width="100%",
                         src="data:image/png;base64, " + pil_to_b64(Image.open(file.data)))
        data = dbc.Card(
            dbc.CardBody(
                [
                    html.H4(f"File Name: {file.name}"),
                    html.H4(f"File Format: {file.format}"),
                    html.H4(f"File Size: {file.size}"),
                    html.Div([image]),
                ],))
        return data
    else:
        return html.Div()


def slide_show():
    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Button(html.I(className="bi bi-arrow-left"), id="previous", class_name="align-text-end"),),
            dbc.Col(html.Div(id="current_image")),
            dbc.Col(dbc.Button(html.I(className="bi bi-arrow-right"), id="next")),
        ])
    ], className="d-flex justify-content-center")

#################
#   Callbacks   #
#################

# callback for directory deletion modal view and executing directory deletion
@callback([Output('current_image', 'children'), Output('image_counter','data')],
          [Input('previous', 'n_clicks'), Input('next', 'n_clicks'),
          State('directory', 'data'), State('project', 'data'), State('image_counter', 'data')])
def modal_and_directory_deletion(previous, next, directory_name, project_name, image_counter):
    image_counter = image_counter or {'counter': 0}
    if ctx.triggered_id == "previous":
        if image_counter['counter'] == 0:
            return no_update, no_update
        else:
            with get_connection() as connection:
                directory = connection.get_project(project_name).get_directory(directory_name)
                image_counter['counter'] = image_counter['counter'] - 1
                file = directory.get_all_files()[image_counter['counter']]
            return show_image(file), image_counter
    elif ctx.triggered_id == "next":
        with get_connection() as connection:
            directory = connection.get_project(project_name).get_directory(directory_name)
            if image_counter['counter'] == len(directory.get_all_files()):
                pass
            else:
                image_counter['counter'] = image_counter['counter'] + 1
                file=directory.get_all_files()[image_counter['counter']]
                return show_image(file), image_counter
    else:
        return no_update, no_update


#################
#  Page Layout  #
#################


def layout(project_name=None, directory_name=None):
    try:
        with get_connection() as connection:
            project = connection.get_project(project_name)
            directory = project.get_directory(directory_name)
    except:
        return dbc.Alert("No Directory found", color="danger")
    return html.Div([
        dcc.Store(id='directory', data=directory.name),
        dcc.Store(id='project', data=project.name),
        dcc.Store(id='image_counter'),
        dbc.Row([
                dbc.Col(html.H1(f"Directory {directory.name}", style={
                    'textAlign': 'left', })),
                ], className="mb-3"),
        slide_show(),
    ])
