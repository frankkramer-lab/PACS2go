from tempfile import TemporaryDirectory
from typing import Optional

import dash_bootstrap_components as dbc
from dash import (Input, Output, State, callback, ctx, dcc, html, no_update,
                  register_page)
from dash.exceptions import PreventUpdate
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulAttributeUpdateException,
    UnsuccessfulDeletionException, UnsuccessfulGetException)
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import (colors, format_linebreaks, get_connection,
                                      login_required_interface)

register_page(__name__, title='Project - PACS2go',
              path_template='/project/<project_name>')


def get_details(project: Project):
    description = "Description: " + project.description
    keywords = "Keywords: " + project.keywords
    parameters = "Parameters: \n " + project.parameters
    formatted_parameters = format_linebreaks(parameters)
    time = "Created on: " + project.timestamp_creation.strftime(
        "%dth %B %Y, %H:%M:%S") + " | Last updated on: " + project.last_updated.strftime("%dth %B %Y, %H:%M:%S")
    owners = "Owners: " + ', '.join(project.owners)
    user_role = "You're part of the '" + project.your_user_role.capitalize() + \
        "' user group."
    #citations = project.citations if project.citations else ''
    return [html.H6(description), html.H6(keywords), html.H6(formatted_parameters), html.H6(time), html.H6(owners), html.H6(user_role), html.H6("Citations:"), html.Div(id='citation-list')]


def get_directories_table(project: Project, filter: str = ''):
    # Get list of all directory names and number of files per directory
    rows = []
    for d in project.get_all_directories():
        # Only show rows if no filter is applied of if the filter has a match in the directory's name
        if filter.lower() in d.name.lower() or len(filter) == 0:
            # Directory names represent links to individual directory pages
            rows.append(html.Tr([html.Td(dcc.Link(d.display_name, href=f"/dir/{project.name}/{d.name}", className="text-decoration-none", style={'color': colors['links']})), html.Td(
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


def modal_delete(project: Project):
    if project.your_user_role == 'Owners':
        # Modal view for project deletion
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-trash me-2"),
                        "Delete Project"], id="delete_project", size="md", color="danger"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Delete Project {project.name}")),
                    dbc.ModalBody([
                        html.Div(id="delete-project-content"),
                        dbc.Label(
                            "Are you sure you want to delete this project and all its data?"),
                        dbc.Input(id="project", value=project.name,
                                  disabled=True),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the deletion of a project (see modal_and_project_creation)
                        dbc.Button("Delete Project",
                                   id="delete_and_close", color="danger"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_delete"),
                    ]),
                ],
                id="modal_delete",
                is_open=False,
            ),
        ])


def modal_delete_data(project: Project):
    # Modal view for deleting all directories of a project
    if project.your_user_role == 'Owners':
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-trash me-2"),
                        "Delete All Directories"], id="delete_project_data", size="md", color="danger"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Delete All Project {project.name} Directories")),
                    dbc.ModalBody([
                        html.Div(id="delete-project-data-content"),
                        dbc.Label(
                            "Are you sure you want to delete all directories of this project? This will empty the entire project."),
                        dbc.Input(id="project_2",
                                  value=project.name, disabled=True),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the directory deletion (see modal_and_project_creation)
                        dbc.Button("Delete All Directories",
                                   id="delete_data_and_close", color="danger"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_delete_data"),
                    ]),
                ],
                id="modal_delete_data",
                is_open=False,
            ),
        ])


def modal_edit_project(project: Project):
    if project.your_user_role == 'Owners':
        # Modal view for project editing
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-pencil me-2"),
                        "Edit Project"], id="edit_project", size="md", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Edit Project {project.name}")),
                    dbc.ModalBody([
                        html.Div(id='edit-project-content'),
                        dbc.Label(
                            "Please enter a new description for your project.", class_name="mt-2"),
                        # Input Text Field for project name
                        dbc.Input(id="new_project_description",
                                  placeholder=project.description, value=project.description),
                        dbc.Label(
                            "Please enter searchable keywords. Each word, separated by a space, can be individually used as a search string.", class_name="mt-2"),
                        # Input Text Field for project name
                        dbc.Input(id="new_project_keywords",
                                  placeholder=project.keywords, value=project.keywords),
                        dbc.Label(
                            "Please enter desired parameters.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Textarea(id="new_project_parameters",
                                  placeholder="...", value=project.parameters),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the update of a project
                        dbc.Button("Save changes",
                                   id="edit_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_edit")
                    ]),
                ],
                id="modal_edit_project",
                is_open=False,
            ),
        ])


def modal_create_new_directory(project:Project):
    # Modal view for project creation
    if project.your_user_role == 'Owners' or project.your_user_role == 'Members':
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-plus me-2"),
                        "Create Directory"], id="create_new_directory_btn", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Create New Directory")),
                    dbc.ModalBody([
                        html.Div(id='create-directory-content'),
                        dbc.Label(
                            "Please enter a unique name. (Don't use ä,ö,ü or ß)"),
                        # Input Text Field for project name
                        dbc.Input(id="new_dir_name",
                                placeholder="Directory unique name...", required=True),
                        dbc.Label(
                            "Please enter desired parameters.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Textarea(id="new_dir_parameters",
                                placeholder="..."),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Create Directory",
                                id="create_dir_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_create_dir")
                    ]),
                ],
                id="modal_create_new_directory",
                is_open=False,
            ),
        ])


def insert_data(project: Project):
    if project.your_user_role == 'Owners' or project.your_user_role == 'Members':
        # Link to Upload functionality with a set project name
        return html.Div(dbc.Button([html.I(className="bi bi-cloud-upload me-2"),
                        "Insert Data"], href=f"/upload/{project.name}", size="md", color="success"))


def download_project_data():
    return html.Div([
        dbc.Button([
            html.I(className="bi bi-download me-2"), "Download"], id="btn_download_project", size="md"),
        dbc.Spinner(dcc.Download(id="download_project"))])


#################
#   Callbacks   #
#################

@callback(
    [Output('modal_delete', 'is_open'),
     Output('delete-project-content', 'children')],
    [Input('delete_project', 'n_clicks'),
     Input('close_modal_delete', 'n_clicks'),
     Input('delete_and_close', 'n_clicks')],
    State("modal_delete", "is_open"),
    State("project", "value"),
    prevent_initial_call=True)
# Callback for project deletion modal view and executing project deletion
def modal_and_project_deletion(open, close, delete_and_close, is_open, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "delete_project" or ctx.triggered_id == "close_modal_delete":
        return not is_open, no_update

    if ctx.triggered_id == "delete_and_close":
        try:
            connection = get_connection()
            project = connection.get_project(project_name)

            if project:
                project.delete_project()

            return is_open, dbc.Alert([f"The project {project.name} has been successfully deleted! ",
                                       dcc.Link(f"Click here to go to back to the projects overview.",
                                                href=f"/projects",
                                                className="fw-bold text-decoration-none",
                                                style={'color': colors['links']})], color="success")

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
            return is_open, dbc.Alert(str(err), color="danger")
    else:
        raise PreventUpdate


@callback(
    [Output('modal_delete_data', 'is_open'),
     Output('delete-project-data-content', 'children'),
     Output('directory_table', 'children', allow_duplicate=True), ],
    [Input('delete_project_data', 'n_clicks'),
     Input('close_modal_delete_data', 'n_clicks'),
     Input('delete_data_and_close', 'n_clicks')],
    State("modal_delete_data", "is_open"),
    State("project_2", "value"),
    prevent_initial_call=True)
# Callback used to delete all directories of a project (open modal view + actual deletion)
def modal_and_project_data_deletion(open, close, delete_data_and_close, is_open, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "delete_project_data" or ctx.triggered_id == "close_modal_delete_data":
        return not is_open, no_update, no_update

    # Delete Button in Modal View
    if ctx.triggered_id == "delete_data_and_close":
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            if project:
                dirs = project.get_all_directories()
                if len(dirs) == 0:
                    return is_open,  dbc.Alert("Project is empty.", color="danger"), no_update
                else:
                    for d in dirs:
                        d.delete_directory()
                    return not is_open, no_update, get_directories_table(project)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    [Output('modal_edit_project', 'is_open'),
     Output('edit-project-content', 'children'),
     Output('details_card', 'children')],
    [Input('edit_project', 'n_clicks'),
     Input('close_modal_edit', 'n_clicks'),
     Input('edit_and_close', 'n_clicks')],
    State("modal_edit_project", "is_open"),
    State('project_store', 'data'),
    State('new_project_description', 'value'),
    State('new_project_keywords', 'value'),
    State('new_project_parameters', 'value'),
    prevent_initial_call=True)
# Callback used to edit project description, parameters and keywords
def modal_edit_project_callback(open, close, edit_and_close, is_open, project_name, description, keywords, parameters):
    # Open/close modal via button click
    if ctx.triggered_id == "edit_project" or ctx.triggered_id == "close_modal_edit":
        return not is_open, no_update, no_update

    # User does everything "right"
    elif ctx.triggered_id == "edit_and_close":
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            if description:
                # Set new description
                project.set_description(description)
            if keywords:
                # Set new keywords
                project.set_keywords(keywords)
            if parameters:
                # Set new parameter string
                project.set_parameters(parameters)
            project = connection.get_project(project_name)
            return not is_open, no_update, get_details(project)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate

# Callback for project creation modal view and executing project creation


@callback(
    [Output('modal_create_new_directory', 'is_open'),
     Output('create-directory-content', 'children'),
     Output('directory_table', 'children', allow_duplicate=True)],
    [Input('create_new_directory_btn', 'n_clicks'),
     Input('close_modal_create_dir', 'n_clicks'),
     Input('create_dir_and_close', 'n_clicks')],
    State("modal_create_new_directory", "is_open"),
    State('new_dir_name', 'value'),
    State('new_dir_parameters', 'value'),
    State("project", "value"),
    prevent_initial_call=True)
def modal_and_directory_creation(open, close, create_and_close, is_open, name, parameters, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "create_new_directory_btn" or ctx.triggered_id == "close_modal_create_dir":
        return not is_open, no_update, no_update

    # User tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "create_dir_and_close" and name is None:
        return is_open, dbc.Alert("Please specify a name.", color="danger"), no_update

    # User does everything "right" for project creation
    elif ctx.triggered_id == "create_dir_and_close" and name is not None:
        # Project name cannot contain whitespaces
        name = str(name).replace(" ", "_")
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            directory = project.create_directory(name, parameters)
            return is_open, dbc.Alert([html.Span("A new directory has been successfully created! "),
                                       html.Span(dcc.Link(f" Click here to go to the new directory {directory.display_name}.",
                                                          href=f"/dir/{project.name}/{directory.name}",
                                                          className="fw-bold text-decoration-none",
                                                          style={'color': colors['links']}))], color="success"), get_directories_table(project)

        except Exception as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate

@callback(
    Output('citation-list', 'children'),
    [Input('project_store', 'data')]
)
def update_citation_list(project_name):
    try:
        connection = get_connection()
        project = connection.get_project(project_name)
        citations = project.citations
        citation_list = html.Ul([
            html.Li(f"{index+1}. {citation.citation} - {citation.link}")
            for index, citation in enumerate(citations)
        ])
        return citation_list
    except Exception as err:
        return html.P(f"Error retrieving citations: {str(err)}")


@callback(
    Output('directory_table', 'children'),
    Input('filter_directory_tags_btn', 'n_clicks'),
    Input('filter_directory_tags', 'value'),
    State('project_store', 'data'),
    prevent_initial_call=True)
def filter_directory_table(btn, filter, project_name):
    # Apply filter to the directories table
    if ctx.triggered_id == 'filter_directory_tags_btn' or filter:
        if filter or filter == "":
            try:
                connection = get_connection()
                return get_directories_table(connection.get_project(project_name), filter)
            except (FailedConnectionException, UnsuccessfulGetException) as err:
                return dbc.Alert(str(err), color="danger")
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate


@callback(
    Output("download_project", "data"),
    Input("btn_download_project", "n_clicks"),
    State("project_store", "data"),
    prevent_initial_call=True,
)
def download_project(n_clicks, project_name):
    if ctx.triggered_id == 'btn_download_project':
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            with TemporaryDirectory() as tempdir:
                # Get directory as zip to a tempdir and then send it to browser
                zipped_project_data = project.download(tempdir)
                return dcc.send_file(zipped_project_data)

        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")

    else:
        raise PreventUpdate


#################
#  Page Layout  #
#################

def layout(project_name: Optional[str] = None):
    if not current_user.is_authenticated:
        return login_required_interface()

    if project_name:
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")
        return html.Div([
            dcc.Store(id='project_store', data=project.name),

            # Breadcrumbs
            html.Div(
                [
                    dcc.Link("Home", href="/",
                             style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    dcc.Link("All Projects", href="/projects",
                             style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span(f"{project.name}", className='active fw-bold',
                              style={"color": "#707070"})
                ],
                className='breadcrumb'
            ),

            # Header including page title and action buttons
            dbc.Row([
                dbc.Col(html.H1(f"Project {project.name}", style={
                        'textAlign': 'left', })),
                dbc.Col(
                    [insert_data(project),
                        download_project_data(),
                        modal_delete(project),
                        modal_delete_data(project)], className="d-grid gap-2 d-md-flex justify-content-md-end"),
            ], className="mb-3"),

            # Project Information (owners,..)
            dbc.Card([
                dbc.CardHeader(
                    children=[
                        html.H4("Details"),
                        modal_edit_project(project)],
                    className="d-flex justify-content-between align-items-center"),
                dbc.Spinner(dbc.CardBody(get_details(project), id="details_card"))], class_name="mb-3"),
            dbc.Card([
                dbc.CardHeader(children=[
                        html.H4("Directories"),
                        modal_create_new_directory(project)],
                    className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    # Filter file tags
                    dbc.Row([
                        dbc.Col(dbc.Input(id="filter_directory_tags",
                            placeholder="Search directory... ")),
                        dbc.Col(dbc.Button(
                            "Filter", id="filter_directory_tags_btn"))
                    ], class_name="mb-3"),
                    # Directories Table
                    dbc.Spinner(html.Div(get_directories_table(
                        project), id='directory_table')),
                ])], class_name="mb-3"),
        ])

    else:
        return dbc.Alert("No Project found.", color="danger")
