import base64
import io
import json
import math
from pacs2go.data_interface.exceptions.exceptions import DownloadException
from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulDeletionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulGetException
from pacs2go.data_interface.pacs_data_interface import Directory
from pacs2go.data_interface.pacs_data_interface import File
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection
from pacs2go.frontend.helpers import login_required_interface
from tempfile import TemporaryDirectory
from typing import Optional

import dash_bootstrap_components as dbc
import pandas as pd
from dash import ALL
from dash import callback
from dash import ctx
from dash import dash_table
from dash import dcc
from dash import get_app
from dash import html
from dash import Input
from dash import no_update
from dash import Output
from dash import register_page
from dash import State
from dash.exceptions import PreventUpdate
from flask_login import current_user

register_page(__name__, title='Directory - PACS2go',
              path_template='/dir/<project_name>/<directory_name>')


def get_single_file_preview(directory: Directory):
    # Preview first image within the directory
    if len(directory.get_all_files()) > 0:
        file = directory.get_all_files()[0]
        file = directory.get_file(file.name)
        if file.format == 'JPEG' or file.format == 'PNG' or file.format == 'TIFF':
            # Display jpeg, png or tiff bytes as image
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
        else:
            return html.Div()

        return dbc.Card([
            dbc.CardHeader("Preview the first file of this directory:"),
            dbc.CardBody(content, className="w-25 h-25")])


def get_files_table(directory: Directory, filter: str = '', active_page: int = 0):
    rows = []
    files = directory.get_all_files()

    # Get file information as rows for table
    for index, f in enumerate(files):
        # Only show rows if no filter is applied of if the filter has a match in the file tags
        if len(filter) == 0 or (len(filter) > 0 and filter.lower() in f.tags.lower()):
            rows.append(html.Tr([html.Td(index+1),
                                 html.Td(dcc.Link(f.name, href=f"/viewer/{directory.project.name}/{directory.name}/{f.name}", className="text-decoration-none", style={'color': colors['links']})
                                         ),
                                html.Td(f.format),
                                html.Td(f.tags),
                                html.Td(
                                    f"{round(f.size/1024,2)} KB ({f.size} Bytes)"),
                                html.Td([modal_delete_file(directory, f), dbc.Button([html.I(className="bi bi-download"), ], id={'type': 'btn_download_file', 'index': f.name})], style={'display': 'flex', 'justifyContent': 'space-evenly', 'alignItems': 'center'})]))

    # Table header
    table_header = [
        html.Thead(
            html.Tr([html.Th(" "), html.Th("File Name"), html.Th("Format"), html.Th("Tags"), html.Th("File Size"), html.Th("Actions")]))
    ]

    # Only show 20 rows at a time - pagination
    table_body = [html.Tbody(
        rows[active_page*20:min((active_page+1)*20, int(directory.number_of_files))])]

    # Put together file table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def modal_delete(directory: Directory):
    if directory.project.your_user_role == 'Owners':
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


def modal_delete_file(directory: Directory, file: File):
    if directory.project.your_user_role == 'Owners':
        # Modal view for directory deletion
        return html.Div([
            dcc.Store('file', data=file.name),
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-trash")],
                       id={'type': 'delete_file', 'index': file.name}, size="md", color="danger"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Delete File")),
                    dbc.ModalBody([
                        html.Div(
                            id='delete-file-content'),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the deletion of the file
                        dbc.Button("Delete File",
                                   id={'type': 'delete_file_and_close', 'index': file.name}, color="danger"),
                        # Button which causes modal to close/disappear
                        dbc.Button(
                            "Close", id='close_modal_delete_file'),
                    ]),
                ],
                id='modal_delete_file',
                is_open=False,
            ),
        ])


#################
#   Callbacks   #
#################

@callback(
    [Output('modal_delete_file', 'is_open'),
     Output('delete-file-content', 'children'), Output('file', 'data')],
    [Input({'type': 'delete_file', 'index': ALL}, 'n_clicks'),
     Input('close_modal_delete_file', 'n_clicks'),
     Input({'type': 'delete_file_and_close', 'index': ALL}, 'n_clicks')],
    [State('modal_delete_file', 'is_open'),
     State('directory', 'data'),
     State('project', 'data'),
     State('file', 'data')],
    prevent_initial_call=True
)
# Callback for the file deletion modal view and the actual file deletion
def modal_and_file_deletion(open, close, delete_and_close, is_open, directory_name, project_name, file_name):
    if isinstance(ctx.triggered_id, dict):
        # Delete Button in File list - open/close Modal View
        if ctx.triggered_id['type'] == "delete_file":
            return not is_open, dbc.Label(
                f"Are you sure you want to delete this file '{ctx.triggered_id['index']}'?"), ctx.triggered_id['index']
        # Delete Button in the Modal View
        if ctx.triggered_id['type'] == 'delete_file_and_close':
            try:
                connection = get_connection()
                file = connection.get_file(
                    project_name, directory_name, file_name)
                # Delete File
                file.delete_file()
                # Close Modal and show message
                return is_open, dbc.Alert(
                    [f"The file {file.name} has been successfully deleted! "], color="success"), no_update
            except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
                return not is_open, dbc.Alert(str(err), color="danger"), no_update

    elif isinstance(ctx.triggered_id, str):
        if ctx.triggered_id == "close_modal_delete_file":
            # Close Modal View
            return not is_open, no_update, no_update

    else:
        raise PreventUpdate


@callback(
    [Output('modal_delete_directory', 'is_open'),
     Output('delete-directory-content', 'children')],
    [Input('delete_directory', 'n_clicks'),
     Input('close_modal_delete_directory', 'n_clicks'),
     Input('delete_directory_and_close', 'n_clicks')],
    State("modal_delete_directory", "is_open"),
    State('directory', 'data'),
    State('project', 'data'),
    prevent_initial_call=True)
# Callback for the directory deletion modal view and the actual directory deletion
def modal_and_directory_deletion(open, close, delete_and_close, is_open, directory_name, project_name):
    # Open/close Modal View via button click
    if ctx.triggered_id == "delete_directory" or ctx.triggered_id == "close_modal_delete_directory":
        return not is_open, no_update

    # Delete Button in the Modal View
    if ctx.triggered_id == "delete_directory_and_close":
        try:
            connection = get_connection()
            directory = connection.get_directory(
                project_name, directory_name)
            # Delete Directory
            directory.delete_directory()
            # Close Modal View and show message
            return is_open, dbc.Alert([f"The directory {directory.name} has been successfully deleted! ",
                                       dcc.Link(f"Click here to go to back to the '{project_name}' project.",
                                                href=f"/project/{project_name}",
                                                className="fw-bold text-decoration-none",
                                                style={'color': colors['links']})], color="success")
        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
            return is_open, dbc.Alert(str(err), color="danger")

    else:
        raise PreventUpdate


@callback(
    Output('files_table', 'children'),
    Input('filter_file_tags_btn', 'n_clicks'),
    Input('filter_file_tags', 'value'),
    Input('pagination-files', 'active_page'),
    State('directory', 'data'),
    State('project', 'data'),
    prevent_initial_call=True)
# Callback for the file tag filter feature
def filter_files_table(btn, filter, active_page, directory_name, project_name):
    # Filter button is clicked or the input field registers a user input
    if ctx.triggered_id == 'filter_file_tags_btn' or filter or active_page:
        try:
            connection = get_connection()
            directory = connection.get_directory(project_name, directory_name)

            if not active_page:
                active_page = 1
            if not filter:
                filter = ''
            return get_files_table(directory, filter, int(active_page)-1)
        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")
    else:
        raise PreventUpdate


@callback(
    Output("download_directory", "data"),
    Input("btn_download_dir", "n_clicks"),
    State("directory", "data"),
    State("project", "data"),
    prevent_initial_call=True,
)
# Callback for the download (directory) feature
def download(n_clicks, directory_name, project_name):
    # Download button is triggered
    if ctx.triggered_id == 'btn_download_dir':
        try:
            connection = get_connection()
            directory = connection.get_directory(project_name, directory_name)
            with TemporaryDirectory() as tempdir:
                zipped_dir = directory.download(tempdir)
                return dcc.send_file(zipped_dir)
        except (FailedConnectionException, UnsuccessfulGetException, DownloadException) as err:
            return dbc.Alert(str(err), color="danger")
    else:
        raise PreventUpdate


@callback(
    Output("download_single_file", "data"),
    Input({'type': 'btn_download_file', 'index': ALL}, 'n_clicks'),
    State("directory", "data"),
    State("project", "data"),
    prevent_initial_call=True,
)
# Callback for the download (single files) feature
def download_single_file(n_clicks, directory_name, project_name):
    if isinstance(ctx.triggered_id, dict):
        # Download button in the files table is triggered
        if ctx.triggered_id['type'] == 'btn_download_file' and any(n_clicks):
            with TemporaryDirectory() as tempdir:
                try:
                    connection = get_connection()
                    file = connection.get_file(
                        project_name, directory_name, ctx.triggered_id['index'])
                    temp_dest = file.download(destination=tempdir)
                    return dcc.send_file(temp_dest)
                except (FailedConnectionException, UnsuccessfulGetException, DownloadException) as err:
                    return dbc.Alert(str(err), color='warning')
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate


#################
#  Page Layout  #
#################


def layout(project_name: Optional[str] = None, directory_name: Optional[str] = None):
    if not current_user.is_authenticated:
        return login_required_interface()

    if project_name and directory_name:
        try:
            connection = get_connection()
            directory = connection.get_directory(
                project_name, directory_name)

        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")

        return html.Div([
            # dcc Store components for project and directory name strings
            dcc.Store(id='directory', data=directory.name),
            dcc.Store(id='project', data=project_name),

            # Breadcrumbs
            html.Div(
                [
                    dcc.Link(
                        "Home", href="/", style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    dcc.Link("All Projects", href="/projects",
                             style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    dcc.Link(f"{project_name}", href=f"/project/{project_name}",
                             style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span(
                        f"{directory_name}", className='active fw-bold', style={"color": "#707070"})
                ],
                className='breadcrumb'
            ),

            dbc.Row([
                    dbc.Col(
                        html.H1(f"Directory {directory.display_name}", style={
                                'textAlign': 'left', })),
                    dbc.Col(
                        [
                            # Modal for directory deletion
                            modal_delete(directory),
                            html.Div([
                                # Button to access the File Viewer (viewer.py)
                                dbc.Button([html.I(className="bi bi-play me-2"),
                                            "Viewer"], color="success", size="md",
                                           href=f"/viewer/{project_name}/{directory.name}/none"),
                                # Download Directory button
                                dbc.Button([html.I(className="bi bi-download me-2"),
                                            "Download"], id="btn_download_dir", size="md", class_name="mx-2"),
                                # dcc download components for downloading directories and files
                                dcc.Download(id="download_directory"), dcc.Download(id="download_single_file")])
                        ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
                    ], className="mb-3"),

            # Files Table
            dbc.Card([
                dbc.CardHeader('Files'),
                dbc.CardBody([
                    # Filter file tags
                    dbc.Row([
                        dbc.Col(dbc.Input(id="filter_file_tags",
                            placeholder="Search file tags.. (e.g. 'CT')")),
                        dbc.Col(dbc.Button(
                            "Filter", id="filter_file_tags_btn"))
                    ], class_name="mb-3"),

                    # Display a table of the directory's files
                    dbc.Spinner(html.Div(get_files_table(
                        directory), id='files_table')),
                    dbc.Pagination(id="pagination-files", max_value=math.ceil(
                        int(directory.number_of_files)/20), first_last=True, previous_next=True)
                ])], class_name="mb-3"),

            # Display a preview of the first file's content
            get_single_file_preview(directory),
        ])

    else:
        return dbc.Alert("No project and directory name was given.", color="danger")
