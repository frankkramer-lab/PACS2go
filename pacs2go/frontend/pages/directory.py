import base64
import io
import json
import math
from tempfile import TemporaryDirectory
from typing import Optional

import dash_bootstrap_components as dbc
import pandas as pd
from dash import (ALL, Input, Output, State, callback, ctx, dash_table, dcc,
                  html, no_update, register_page)
from dash.exceptions import PreventUpdate
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    DownloadException, FailedConnectionException, UnsuccessfulAttributeUpdateException,
    UnsuccessfulDeletionException, UnsuccessfulGetException)
from pacs2go.data_interface.pacs_data_interface import Directory, File, Project
from pacs2go.frontend.helpers import (colors, format_linebreaks, get_connection,
                                      login_required_interface)

register_page(__name__, title='Directory - PACS2go',
              path_template='/dir/<project_name>/<directory_name>')


def get_details(directory: Directory):
    detail_data = []
    if directory.parameters:
        formatted_parameters = format_linebreaks(directory.parameters)
        parameters = [html.B("Parameters: "), html.Br()] + formatted_parameters
        detail_data.append(html.H6(parameters))

    time = html.B("Created on: "), directory.timestamp_creation.strftime(
        "%dth %B %Y, %H:%M:%S"), html.B(" | Last updated on: "), directory.last_updated.strftime("%dth %B %Y, %H:%M:%S")
    detail_data.append(html.H6(time))

    return detail_data

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
        tags = f.tags if f.tags else ''
        if len(filter) == 0 or (len(filter) > 0 and filter.lower() in tags.lower()):
            rows.append(html.Tr([html.Td(index+1),
                                 html.Td(dcc.Link(f.name, href=f"/viewer/{directory.project.name}/{directory.name}/{f.name}", className="text-decoration-none", style={'color': colors['links']})
                                         ),
                                html.Td(f.format),
                                html.Td(f.modality),
                                html.Td(
                                    f"{round(f.size/1024,2)} KB ({f.size} Bytes)"),
                                html.Td(f.timestamp_creation.strftime(
                                    "%dth %B %Y, %H:%M:%S")),
                                html.Td(tags),
                                html.Td([modal_delete_file(directory, f), modal_edit_file(f), dbc.Button([html.I(className="bi bi-download")], id={'type': 'btn_download_file', 'index': f.name})], style={'display': 'flex', 'justifyContent': 'space-evenly', 'alignItems': 'center'})]))

    # Table header
    table_header = [
        html.Thead(
            html.Tr([html.Th(" "), html.Th("File Name"), html.Th("Format"),  html.Th("Modality"), html.Th("File Size"), html.Th("Uploaded on"), html.Th("Tags"), html.Th("Actions")]))
    ]

    # Only show 20 rows at a time - pagination
    table_body = [html.Tbody(
        rows[active_page*20:min((active_page+1)*20, int(directory.number_of_files))])]

    # Put together file table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def get_subdirectories_table(directory: Directory, filter: str = ''):
    # Get list of all directory names and number of files per directory
    rows = []
    for d in directory.get_subdirectories():
        # Only show rows if no filter is applied of if the filter has a match in the directory's name
        if filter.lower() in d.display_name.lower() or len(filter) == 0:
            # Directory names represent links to individual directory pages
            rows.append(html.Tr([html.Td(dcc.Link(d.display_name, href=f"/dir/{directory.project.name}/{d.name}", className="text-decoration-none", style={'color': colors['links']})), html.Td(
                d.number_of_files), html.Td(d.timestamp_creation.strftime("%dth %B %Y, %H:%M:%S")), html.Td(d.last_updated.strftime("%dth %B %Y, %H:%M:%S"))]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Directory Name"), html.Th("Number of Files"), html.Th("Created on"), html.Th("Last Updated on")]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together directory table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def modal_create_new_subdirectory(directory):
    if directory.project.your_user_role == 'Owners':
        # Modal view for subdir creation
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-plus me-2"),
                        "Create Sub-Directory"], id="create_new_subdirectory_btn", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        "Create New Sub-Directory")),
                    dbc.ModalBody([
                        html.Div(id='create-subdirectory-content'),
                        dbc.Label(
                            "Please enter a unique name. (Don't use ä,ö,ü or ß)"),
                        # Input Text Field for project name
                        dbc.Input(id="new_subdir_name",
                                  placeholder="Directory unique name...", required=True),
                        dbc.Label(
                            "Please enter desired parameters.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Textarea(id="new_subdir_parameters",
                                  placeholder="..."),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Create Directory",
                                   id="create_subdir_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_create_subdir")
                    ]),
                ],
                id="modal_create_new_subdirectory",
                is_open=False,
            ),
        ])


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
    
def modal_edit_directory(project: Project, directory: Directory):
    # Modal view for project creation
    if project.your_user_role == 'Owners' or project.your_user_role == 'Members':
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-pencil me-2"),
                        "Edit Directory"], id="edit_directory_metadata", size="md", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(f"Edit Directory {directory.display_name}")),
                    dbc.ModalBody([
                        html.Div(id='edit_directory_metadata_content'),
                        dbc.Label(
                            "Please enter desired parameters.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Textarea(id="edit_directory_parameters",
                                placeholder="...", value=directory.parameters),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Update Directory Metadata",
                                id="edit_dir_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_edit_dir")
                    ]),
                ],
                id="modal_edit_directory_metadata",
                is_open=False,
            ),
        ])

def modal_edit_file(file:File):
    # Modal view for project creation
    if file.directory.project.your_user_role == 'Owners' or file.directory.project.your_user_role == 'Members':
        return html.Div([
            dcc.Store('file_for_edit', data=file.name),
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-pencil")], id={'type': 'edit_file_in_list', 'index': file.name}, size="md", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(f"Edit File")),
                    dbc.ModalBody([
                        html.Div(id='edit_file_in_list_content'),
                        dbc.Label(
                            "Please enter desired modality.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Input(id="edit_file_in_list_modality",
                                placeholder="e.g.: CT, MRI", value=file.modality),
                        dbc.Label(
                            "Please enter desired tags.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Input(id="edit_file_in_list_tags",
                                placeholder="e.g.: Dermatology, control group", value=file.tags),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Update Directory Metadata",
                                id={'type': 'edit_file_in_list_and_close', 'index': file.name}, color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_edit_file_in_list")
                    ]),
                ],
                id="modal_edit_file_in_list",
                is_open=False,
            ),
        ])


#################
#   Callbacks   #
#################

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
    [Output('modal_edit_directory_metadata', 'is_open'),
     Output('edit_directory_metadata_content', 'children'),
     Output('dir_details_card', 'children')],
    [Input('edit_directory_metadata', 'n_clicks'),
     Input('close_modal_edit_dir', 'n_clicks'),
     Input('edit_dir_and_close', 'n_clicks')],
    State("modal_edit_directory_metadata", "is_open"),
    State('project', 'data'),
    State('directory', 'data'),
    State('edit_directory_parameters', 'value'),
    prevent_initial_call=True)
# Callback used to edit project description, parameters and keywords
def modal_edit_directory_callback(open, close, edit_and_close, is_open, project_name, directory_name, parameters):
    # Open/close modal via button click
    if ctx.triggered_id == "edit_directory_metadata" or ctx.triggered_id == "close_modal_edit_dir":
        return not is_open, no_update, no_update

    # User does everything "right"
    elif ctx.triggered_id == "edit_dir_and_close":
        try:
            connection = get_connection()
            directory = connection.get_directory(project_name, directory_name)
            if parameters:
                # Set new parameters
                directory.set_parameters(parameters)
            # Retrieve updated directory to forece reload
            directory = connection.get_directory(project_name, directory_name)
            return not is_open, no_update, get_details(directory)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate

@callback(
    [Output('modal_create_new_subdirectory', 'is_open'),
     Output('create-subdirectory-content', 'children'),
     Output('subdirectory_table', 'children', allow_duplicate=True),],
    [Input('create_new_subdirectory_btn', 'n_clicks'),
     Input('close_modal_create_subdir', 'n_clicks'),
     Input('create_subdir_and_close', 'n_clicks')],
    State("modal_create_new_subdirectory", "is_open"),
    State('new_subdir_name', 'value'),
    State('new_subdir_parameters', 'value'),
    State("directory", "data"),
    State("project", "data"),
    prevent_initial_call=True)
def modal_and_subdirectory_creation(open, close, create_and_close, is_open, name, parameters, directory_name, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "create_new_subdirectory_btn" or ctx.triggered_id == "close_modal_create_subdir":
        return not is_open, no_update, no_update

    # User tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "create_subdir_and_close" and name is None:
        return is_open, dbc.Alert("Please specify a name.", color="danger"), no_update

    # User does everything "right" for project creation
    elif ctx.triggered_id == "create_subdir_and_close" and name is not None:
        # Directory name cannot contain whitespaces
        name = str(name).replace(" ", "_")
        try:
            connection = get_connection()
            directory = connection.get_directory(project_name, directory_name)
            sd = directory.create_subdirectory(name, parameters)

            return is_open, dbc.Alert([html.Span("A new sub-directory has been successfully created! "),
                                       html.Span(dcc.Link(f" Click here to go to the new directory {sd.display_name}.",
                                                          href=f"/dir/{project_name}/{sd.name}",
                                                          className="fw-bold text-decoration-none",
                                                          style={'color': colors['links']}))], color="success"), get_subdirectories_table(directory)

        except Exception as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    Output('subdirectory_table', 'children'),
    Input('filter_subdirectory_tags_btn', 'n_clicks'),
    Input('filter_subdirectory_tags', 'value'),
    State('directory', 'data'),
    State('project', 'data'),
    prevent_initial_call=True)
def filter_directory_table(btn, filter, directory_name, project_name):
    # Apply filter to the directories table
    if ctx.triggered_id == 'filter_directory_tags_btn' or filter:
        if filter or filter == "":
            try:
                connection = get_connection()
                return get_subdirectories_table(connection.get_directory(project_name, directory_name), filter)
            except (FailedConnectionException, UnsuccessfulGetException) as err:
                return dbc.Alert(str(err), color="danger")
        else:
            raise PreventUpdate
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

@callback(
    [Output('modal_delete_file', 'is_open'),
     Output('delete-file-content', 'children'), Output('file', 'data'),
     Output('files_table', 'children', allow_duplicate=True),],
    [Input({'type': 'delete_file', 'index': ALL}, 'n_clicks'),
     Input('close_modal_delete_file', 'n_clicks'),
     Input({'type': 'delete_file_and_close', 'index': ALL}, 'n_clicks')],
    [State('modal_delete_file', 'is_open'),
     State('directory', 'data'),
     State('project', 'data'),
     State('file', 'data'),
     State('pagination-files', 'active_page')],
    prevent_initial_call=True
)
# Callback for the file deletion modal view and the actual file deletion
def modal_and_file_deletion(open, close, delete_and_close, is_open, directory_name, project_name, file_name, page):
    if any(item is not None for item in open):
        if isinstance(ctx.triggered_id, dict):
            # Delete Button in File list - open/close Modal View
            if ctx.triggered_id['type'] == "delete_file":
                return not is_open, dbc.Label(
                    f"Are you sure you want to delete this file '{ctx.triggered_id['index']}'?"), ctx.triggered_id['index'], no_update
            # Delete Button in the Modal View
            if ctx.triggered_id['type'] == 'delete_file_and_close':
                try:
                    connection = get_connection()
                    directory = connection.get_directory(project_name, directory_name)
                    file = directory.get_file(file_name)
                    # Delete File
                    file.delete_file()
                    # Close Modal and show message
                    return is_open, dbc.Alert(
                        [f"The file {file.name} has been successfully deleted! "], color="success"), no_update, get_files_table(directory, active_page=page if page==0 else page - 1)
                except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
                    return not is_open, dbc.Alert(str(err), color="danger"), no_update, no_update

        elif isinstance(ctx.triggered_id, str):
            if ctx.triggered_id == "close_modal_delete_file":
                # Close Modal View
                return not is_open, no_update, no_update, no_update
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate

@callback(
    [Output('modal_edit_file_in_list', 'is_open'),
     Output('edit_file_in_list_content', 'children'), Output('file_for_edit', 'data'),
     Output('files_table', 'children', allow_duplicate=True),],
    [Input({'type': 'edit_file_in_list', 'index': ALL}, 'n_clicks'),
     Input('close_modal_edit_file_in_list', 'n_clicks'),
     Input({'type': 'edit_file_in_list_and_close', 'index': ALL}, 'n_clicks')],
    [State('modal_edit_file_in_list', 'is_open'),
     State('directory', 'data'),
     State('project', 'data'),
     State('file_for_edit', 'data'),
     State('edit_file_in_list_modality', 'value'),
     State('edit_file_in_list_tags', 'value'),
     State('pagination-files', 'active_page')],
    prevent_initial_call=True
)
# Callback for the file deletion modal view and the actual file deletion
def modal_and_file_edit(open, close, edit_and_close, is_open, directory_name, project_name, file_name, modality, tags, page):
    if any(item is not None for item in open):
        if isinstance(ctx.triggered_id, dict):
            # Delete Button in File list - open/close Modal View
            if ctx.triggered_id['type'] == "edit_file_in_list":
                return not is_open, dbc.Label(
                    f"Are you sure you want to edit this file '{ctx.triggered_id['index']}'?"), ctx.triggered_id['index'], no_update
            # Delete Button in the Modal View
            if ctx.triggered_id['type'] == 'edit_file_in_list_and_close':
                try:
                    connection = get_connection()
                    print(page)
                    directory = connection.get_directory(project_name, directory_name)
                    file = directory.get_file(file_name)
                    if modality:
                        file.set_modality(modality)
                    if tags:
                        file.set_tags(tags)
                    return not is_open, dbc.Alert(
                        [f"The file {file.name} has been successfully edited! "], color="success"), no_update, get_files_table(directory, active_page=page if page==0 else page - 1)
                except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
                    return not is_open, dbc.Alert(str(err), color="danger"), no_update, no_update

    elif isinstance(ctx.triggered_id, str):
        if ctx.triggered_id == "close_modal_edit_file_in_list":
            # Close Modal View
            return not is_open, no_update, no_update, no_update

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
            project = connection.get_project(project_name)
            directory = project.get_directory(directory_name)

        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")

        # Breadcrumbs for nested directories
        breadcrumb_buffer = None
        link_to_direct_parent = None
        extra_span = None

        if directory_name.count('::') > 1:
            parent = directory.parent_directory.name
            link_to_direct_parent = dcc.Link(f"{parent.rsplit('::')[-1]}", href=f"/dir/{project_name}/{parent}",
                                             style={"color": colors['sage'], "marginRight": "1%"})
            extra_span = html.Span(" > ", style={"marginRight": "1%"})
            if directory_name.count('::') > 2:
                breadcrumb_buffer = html.Span(
                    " ...   \u00A0 >  ", style={"marginRight": "1%"})

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
                    breadcrumb_buffer,
                    link_to_direct_parent,
                    extra_span,
                    html.Span(
                        f"{directory.display_name}", className='active fw-bold', style={"color": "#707070"})
                ],
                className='breadcrumb'
            ),

            # Header + Buttons
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
            # Directory Details
            dbc.Card([
                dbc.CardHeader(
                    children=[
                        html.H4("Details"), 
                        modal_edit_directory(project, directory)],
                    className="d-flex justify-content-between align-items-center"),
                dbc.Spinner(dbc.CardBody(get_details(directory), id="dir_details_card"))], class_name="mb-3"),
            # Sub-Directories Table
            dbc.Card([
                dbc.CardHeader(children=[html.H4('Directories'),
                                         modal_create_new_subdirectory(directory)],
                               className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    # Filter file tags
                    dbc.Row([
                        dbc.Col(dbc.Input(id="filter_subdirectory_tags",
                            placeholder="Search subdirectories...")),
                        dbc.Col(dbc.Button(
                            "Filter", id="filter_subdirectory_tags_btn")),
                    ], class_name="mb-3"),
                    # Directories Table
                    dbc.Spinner(html.Div(get_subdirectories_table(
                        directory), id='subdirectory_table')),
                ])], class_name="mb-3"),

            # Files Table
            dbc.Card([
                dbc.CardHeader(html.H4('Files')),
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
                        int(directory.number_of_files)/20), first_last=True, previous_next=True, active_page=0)
                ])], class_name="mb-3"),

            # Display a preview of the first file's content
            get_single_file_preview(directory),
        ])

    else:
        return dbc.Alert("No project and directory name was given.", color="danger")
