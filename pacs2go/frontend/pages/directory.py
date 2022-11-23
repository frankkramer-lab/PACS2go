from typing import Optional

import dash_bootstrap_components as dbc
from dash import callback
from dash import ctx
from dash import dcc
from dash import html
from dash import Input
from dash import no_update
from dash import Output
from dash import register_page
from dash import State
from PIL import Image

from pacs2go.data_interface.pacs_data_interface import Directory
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection
from pacs2go.frontend.helpers import pil_to_b64

register_page(__name__, title='Directory - PACS2go',
              path_template='/dir/<project_name>/<directory_name>')


# Preview first image within the directory
def get_single_file_preview(directory: Directory):
    file = directory.get_all_files()[0]
    if file.format == 'JPEG':
        image = html.Img(id="my-img", className="image", width="100%",
                         src="data:image/png;base64, " + pil_to_b64(Image.open(file.data)))
        return html.Div([html.H4("Preview:"), image], className="w-25 h-25")
    else:
        return html.Div()


def get_files_table(directory: Directory):
    rows = []
    # Get file information as rows for table
    for f in directory.get_all_files():
        rows.append(html.Tr([html.Td(dcc.Link(f.name, href=f"/viewer/{directory.project.name}/{directory.name}/{f.name}", className="text-decoration-none", style={'color': colors['links']})
                                     ), html.Td(f.format), html.Td(f"{round(f.size/1024,2)} KB ({f.size} Bytes)")]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("File Name"), html.Th("Format"), html.Th("File Size"), ]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together file table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return html.Div([html.H4("Files:"), table])


def modal_delete(directory: Directory):
    # Modal view for directory deletion
    return html.Div([
        # Button which triggers modal activation
        dbc.Button([html.I(className="bi bi-trash me-2"),
                    "Delete Directory"], id="delete_directory", size="md", color="danger"),
        # Actual modal view
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(
                    f"Delete Directory {directory.name}")),
                dbc.ModalBody([
                    html.Div(id="delete-directory-content"),
                    dbc.Label(
                        "Are you sure you want to delete this directory and all its data?"),
                ]),
                dbc.ModalFooter([
                    # Button which triggers the deletion of the directory
                    dbc.Button("Delete Directory",
                               id="delete_directory_and_close", color="danger"),
                    # Button which causes modal to close/disappear
                    dbc.Button("Close", id="close_modal_delete_directory"),
                ]),
            ],
            id="modal_delete_directory",
            is_open=False,
        ),
    ])


#################
#   Callbacks   #
#################


@callback([Output('modal_delete_directory', 'is_open'), Output('delete-directory-content', 'children')],
          [Input('delete_directory', 'n_clicks'), Input(
              'close_modal_delete_directory', 'n_clicks'), Input('delete_directory_and_close', 'n_clicks')],
          State("modal_delete_directory", "is_open"), State('directory', 'data'), State('project', 'data'))
# Callback for the directory deletion modal view and the actual directory deletion
def modal_and_directory_deletion(open, close, delete_and_close, is_open, directory_name, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "delete_directory" or ctx.triggered_id == "close_modal_delete_directory":
        return not is_open, no_update

    # Delete Button in the Modal View
    if ctx.triggered_id == "delete_directory_and_close":
        try:
            with get_connection() as connection:
                directory = connection.get_directory(project_name, directory_name)
                # Delete Directory
                directory.delete_directory()
                # Redirect to project after deletion
                return not is_open, dcc.Location(href=f"/project/{project_name}", id="redirect_after_directory_delete")

        except Exception as err:
            return is_open, dbc.Alert("Can't be deleted " + str(err), color="danger")
    else:
        return is_open, no_update


#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None, directory_name: Optional[str] = None):
    try:
        if project_name and directory_name:
            with get_connection() as connection:
                directory = connection.get_directory(
                    project_name, directory_name)
                return html.Div([
                    # dcc Store components for project and directory name strings
                    dcc.Store(id='directory', data=directory.name),
                    dcc.Store(id='project', data=project_name),
                    dbc.Row([
                            dbc.Col(
                                html.H1(f"Directory {directory.name}", style={
                                        'textAlign': 'left', })),
                            dbc.Col(
                                [
                                    # Modal for directory deletion
                                    modal_delete(directory),
                                    # Button to access the File Viewer (viewer.py)
                                    dbc.Button([html.I(className="bi bi-play me-2"),
                                                "Viewer"], color="success",
                                               href=f"/viewer/{project_name}/{directory.name}/none"),
                                ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
                            ], className="mb-3"),
                    # Link back to project
                    dcc.Link(
                        html.H4(f"Belongs to project: {project_name}"), href=f"/project/{project_name}",
                        className="mb-3 fw-bold text-decoration-none", style={'color': colors['links']}),
                    # Display a table of all the project's directories
                    get_files_table(directory),
                    # Display a preview of the first file's content
                    get_single_file_preview(directory),
                ])
        else:
            raise Exception("No project and directory name was given.")
    except:
        return dbc.Alert("No Directory found", color="danger")
