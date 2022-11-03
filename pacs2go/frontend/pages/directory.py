from dash import html, callback, Input, Output, register_page, ctx, State, no_update, dcc
from pacs2go.data_interface.pacs_data_interface import Directory
import dash_bootstrap_components as dbc
from pacs2go.frontend.helpers import get_connection, colors, pil_to_b64
from PIL import Image

register_page(__name__, title='Directory - PACS2go',
              path_template='/dir/<project_name>/<directory_name>')


# preview first image within the directory
def get_single_file_preview(directory:Directory):
    file = directory.get_all_files()[0]
    if file.format == 'JPEG':
        image = html.Img(id="my-img",className="image", width="100%", src="data:image/png;base64, " + pil_to_b64(Image.open(file.data)))
        return html.Div([html.H4("Preview:"), image], className="w-25 h-25")
    else:
        return html.Div()

# show table of the directories files and their details
def get_files_table(directory: Directory):
    rows = []
    for f in directory.get_all_files():
        rows.append(html.Tr([html.Td(f.name),html.Td(f.format), html.Td(f.size/1000)]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("File Name"), html.Th("Format"),html.Th("File Size (in Bytes)"),]))
    ]

    table_body = [html.Tbody(rows)]

    # put together file table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return html.Div([html.H4("Files:"), table])

def modal_delete(directory: Directory):
    # modal view for directory deletion
    return html.Div([
        # button which triggers modal activation
        dbc.Button([html.I(className="bi bi-trash me-2"),
                    "Delete Directory"], id="delete_directory", size="md", color="danger"),
        # actual modal view
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
                    # button which triggers the deletion of the directory
                    dbc.Button("Delete Directory",
                               id="delete_directory_and_close", color="danger"),
                    # button which causes modal to close/disappear
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

# callback for directory deletion modal view and executing directory deletion
@callback([Output('modal_delete_directory', 'is_open'), Output('delete-directory-content', 'children')],
          [Input('delete_directory', 'n_clicks'), Input(
              'close_modal_delete_directory', 'n_clicks'), Input('delete_directory_and_close', 'n_clicks')],
          State("modal_delete_directory", "is_open"), State('directory', 'data'), State('project', 'data'))
def modal_and_directory_deletion(open, close, delete_and_close, is_open, directory_name, project_name):
    # open/close modal via button click
    if ctx.triggered_id == "delete_directory" or ctx.triggered_id == "close_modal_delete_directory":
        return not is_open, no_update
    if ctx.triggered_id == "delete_directory_and_close":
        try:
            with get_connection() as connection:
                project = connection.get_project(project_name)
                directory = project.get_directory(directory_name)
                directory.delete_directory()
                # redirect to project after deletion
                return not is_open, dcc.Location(href=f"/project/{project.name}", id="redirect_after_directory_delete")
        except Exception as err:
            return is_open, dbc.Alert("Can't be deleted " + str(err), color="danger")
    else:
        return is_open, no_update

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
        dbc.Row([
            dbc.Col(html.H1(f"Directory {directory.name}", style={
                    'textAlign': 'left', })),
            dbc.Col(
                [
                        modal_delete(directory),
                        dbc.Button([html.I(className="bi bi-play me-2"),
                    "Viewer"], color="success", href=f"/viewer/{project.name}/{directory.name}"),
                ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
        ], className="mb-3"),
        html.H4(f"Belongs to project: {project.name}"),
        get_files_table(directory),
        get_single_file_preview(directory),
    ])