import json
from tempfile import TemporaryDirectory
from typing import Optional

import dash_bootstrap_components as dbc
from dash import (ALL, Input, Output, State, callback, ctx, dcc, html,
                  no_update, register_page)
from dash.exceptions import PreventUpdate
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulAttributeUpdateException,
    UnsuccessfulDeletionException, UnsuccessfulGetException)
from pacs2go.data_interface.pacs_data_interface.project import Project
from pacs2go.data_interface.pacs_data_interface.directory import Directory

from pacs2go.frontend.helpers import (colors, format_linebreaks,
                                      get_connection, login_required_interface)


register_page(__name__, title='Project - PACS2go',
              path_template='/project/<project_name>')


def get_details(project: dict):
    project = json.loads(project)
    detail_data = []
    # Optional Data
    if project['description']:
        description = html.B("Description: "), project['description']
        detail_data.append(html.H6(description))
    if project['keywords']:
        keywords = html.B("Keywords: "), project['keywords']
        detail_data.append(html.H6(keywords))
    if project['parameters']:
        formatted_parameters = format_linebreaks(project['parameters'])
        parameters = [html.B("Parameters: "), html.Br()] + formatted_parameters
        detail_data.append(html.H6(parameters))

    time = html.B("Created on: "), project['timestamp_creation'], html.B(" | Last updated on: "), project['last_updated']
    detail_data.append(html.H6(time))

    owners = html.B("Owners: "), ', '.join(project['owners'])
    detail_data.append(html.H6(owners))

    user_role = "You're part of the '", html.B(
        project['your_user_role'].capitalize()), "' user group."
    detail_data.append(html.H6(user_role))

    return detail_data


def get_directories_table(directories:dict , filter: str = ''):
    # Get list of all directory names and number of files per directory
    directories = json.loads(directories)
    rows = []
    for d in directories:
        # Only show rows if no filter is applied of if the filter has a match in the directory's name
        if filter.lower() in d['display_name'].lower() or len(filter) == 0:
            # Directory names represent links to individual directory pages
            rows.append(html.Tr([
                html.Td(dcc.Link(d['display_name'], href=f"/dir/{d['associated_project']}/{d['unique_name']}",
                        className="text-decoration-none", style={'color': colors['links']})),
                html.Td(d['number_of_files']),
                html.Td(d['timestamp_creation']),
                html.Td(d['last_updated'])
            ]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Directory Name"), html.Th("Number of Files"), html.Th("Created on"), html.Th("Last Updated on")]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together directory table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def get_citations(project: dict):
    project = json.loads(project)

    rows = []

    if project['your_user_role'] == "Owners" or project['your_user_role'] == "Members":
        
        for citation in project['citations']:
            rows.append(html.Tr([
                html.Td(citation['cit_id']),
                html.Td(citation['citation']),
                html.Td(dcc.Link(
                    citation['link'], href=f"{citation['link']}", className="text-decoration-none", style={'color': colors['links']})),
                html.Td(dbc.Button(html.I(className="bi bi-trash"), color="danger",
                        id={'type': 'delete_citation', 'index': citation['cit_id']}))
            ]))

    else:
        for citation in project['citations']:
            rows.append(html.Tr([
                html.Td(citation['cit_id']), 
                html.Td(citation['citation']), 
                html.Td(dcc.Link(
                    citation['link'], href=f"{citation['link']}", className="text-decoration-none", style={'color': colors['links']}))
            ]))

    table_header = [
        html.Thead(html.Tr([html.Th("ID"), html.Th("Citation"), html.Th("Link")]))]

    table_body = [html.Tbody(rows)]

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
                        html.Div(id="delete_project_content"),
                        dbc.Label(
                            "Are you sure you want to delete this project and all its data?"),
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
    
def modal_add_user_to_project(project: Project, users):
    if project.your_user_role == 'Owners':
        # Modal view for project editing
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-plus me-2"),
                        "Add user"], id="add_user_project", size="md", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(
                        f"Add user to Project {project.name}")),
                    dbc.ModalBody([
                        html.Div(id='add_user_project_content'),
                        dbc.Label(
                            "Please enter the username of the user to whom you would like to grant rights.", class_name="mt-2"),
                        # Input Text Field for project name
                        dcc.Dropdown(options=users,id="add_user_project_username"),
                        dbc.Label(
                            "Kindly select the user group to which you wish to add them. Please be aware that adding them to the Owners user group will grant them complete rights, including the ability to delete and reduce the rights of other Owners.", class_name="mt-2"),
                        dcc.Dropdown(options=["Owners","Members", "Collaborators"],id="add_user_project_group",
                          value="Collaborators")

                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the update of a project
                        dbc.Button("Add user.",
                                   id="add_user_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_add_user")
                    ]),
                ],
                id="modal_add_user_project",
                is_open=False,
            ),
        ])


def modal_create_new_directory(project: Project):
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


def modal_add_citation(project: Project):
    if project.your_user_role == 'Owners' or project.your_user_role == 'Members':
        return html.Div([
            # Button which triggers modal activation
            dbc.Button([html.I(className="bi bi-plus me-2"),
                        "Add Citation"], id="add_citation_btn", color="success"),
            # Actual modal view
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle("Add Citation")),
                    dbc.ModalBody([
                        html.Div(id='add_citation_content'),
                        dbc.Label(
                            "Please enter source."),
                        # Input Text Field for project name
                        dbc.Textarea(id="new_cit_citation",
                                     placeholder="Mustermann et al...", required=True),
                        dbc.Label(
                            "If necessary, provide a link.", class_name="mt-2"),
                        # Input Text Field for project parameters
                        dbc.Input(id="new_cit_link",
                                  placeholder="https://www..."),
                    ]),
                    dbc.ModalFooter([
                        # Button which triggers the creation of a project (see modal_and_project_creation)
                        dbc.Button("Add",
                                   id="add_cit_and_close", color="success"),
                        # Button which causes modal to close/disappear
                        dbc.Button("Close", id="close_modal_add_cit")
                    ]),
                ],
                id="modal_create_add_citation",
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
        dcc.Loading(dcc.Download(id="download_project"), color=colors['sage'])])


#################
#   Callbacks   #
#################

@callback(
    [Output('modal_delete', 'is_open'),
     Output('delete_project_content', 'children')],
    [Input('delete_project', 'n_clicks'),
     Input('close_modal_delete', 'n_clicks'),
     Input('delete_and_close', 'n_clicks')],
    State("modal_delete", "is_open"),
    State("project_name", "data"),
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
                    return not is_open, no_update, get_directories_table('{}')

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulDeletionException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    [Output('modal_edit_project', 'is_open'),
     Output('edit-project-content', 'children'),
     Output('details_card', 'children', allow_duplicate=True)],
    [Input('edit_project', 'n_clicks'),
     Input('close_modal_edit', 'n_clicks'),
     Input('edit_and_close', 'n_clicks')],
    State("modal_edit_project", "is_open"),
    State('project_name', 'data'),
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
            project_json = json.dumps(project.to_dict())
            return not is_open, no_update, get_details(project_json)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate

@callback(
    [Output('modal_add_user_project', 'is_open'), 
    Output('add_user_project_content', 'children'),
    Output('details_card', 'children', allow_duplicate=True)],
    [Input('add_user_project', 'n_clicks'),
     Input('close_modal_add_user', 'n_clicks'),
     Input('add_user_and_close', 'n_clicks')],
    State('modal_edit_project', 'is_open'),
    State('add_user_project_username', 'value'),
    State('add_user_project_group', 'value'),
    State('project_name', 'data'),
    prevent_initial_call=True
    )
def modal_add_user_project_callback(open, close, add_and_close, is_open, username, level, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "add_user_project" or ctx.triggered_id == "close_modal_add_user":
        return not is_open, no_update, no_update

    elif ctx.triggered_id == "add_user_and_close" and username and level:
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            if username and level:
                project.grant_rights_to_user(username, level)
            project = connection.get_project(project_name)
            project_json = json.dumps(project.to_dict())
            return False, no_update, get_details(project_json)
        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException) as err:
            return True, dbc.Alert(str(err), color="danger"), no_update

    elif username is None or level is None:
        return True, dbc.Alert("Please insert username and usergroup.", color="warning"), no_update
        
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
    State("project_name", "data"),
    State("dirlist_store", "data"),
    prevent_initial_call=True)
def modal_and_directory_creation(open, close, create_and_close, is_open, name, parameters, project_name, directories_data):
    # Open/close modal via button click
    if ctx.triggered_id == "create_new_directory_btn" or ctx.triggered_id == "close_modal_create_dir":
        return not is_open, no_update, no_update

    # User tries to create modal without specifying a directory name -> show alert feedback
    elif ctx.triggered_id == "create_dir_and_close" and name is None:
        return is_open, dbc.Alert("Please specify a name.", color="danger"), no_update

    # User does everything "right" for directory creation
    elif ctx.triggered_id == "create_dir_and_close" and name is not None:
        # Directory name cannot contain whitespaces
        name = str(name).replace(" ", "_")
        try:
            directories_data = json.loads(directories_data)
            
            connection = get_connection()
            project = connection.get_project(project_name)
            directory = Directory(project=project,name=name,parameters=parameters)
            directories_data.append(directory.to_dict())
            updated_dirlist_json = json.dumps(directories_data)
            
            
            return not is_open, dbc.Alert([html.Span("A new directory has been successfully created! "),
                                       html.Span(dcc.Link(f" Click here to go to the new directory {directory.display_name}.",
                                                          href=f"/dir/{project.name}/{directory.unique_name}",
                                                          className="fw-bold text-decoration-none",
                                                          style={'color': colors['links']}))], color="success"), get_directories_table(updated_dirlist_json)

        except Exception as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    [Output('modal_create_add_citation', 'is_open'),
     Output('add_citation_content', 'children'),
     Output('citation_table', 'children', allow_duplicate=True)],
    [Input('add_citation_btn', 'n_clicks'),
     Input('close_modal_add_cit', 'n_clicks'),
     Input('add_cit_and_close', 'n_clicks')],
    State("modal_create_add_citation", "is_open"),
    State('new_cit_citation', 'value'),
    State('new_cit_link', 'value'),
    State("project_name", "data"),
    prevent_initial_call=True)
def modal_and_add_citation(open, close, create_and_close, is_open, citation, citation_link, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "add_citation_btn" or ctx.triggered_id == "close_modal_add_cit":
        return not is_open, no_update, no_update

    # User tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "add_cit_and_close" and citation is None:
        return is_open, dbc.Alert("Please specify the source.", color="danger"), no_update

    # User does everything "right" for project creation
    elif ctx.triggered_id == "add_cit_and_close" and citation:
        try:
            connection = get_connection()
            project = connection.get_project(project_name)
            project.add_citation(citation, citation_link)
            project_json = json.dumps(project.to_dict())

            return is_open, dbc.Alert([html.Span("A new source has been added! ")], color="success"), get_citations(project_json)

        except Exception as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    Output('citation_table', 'children', allow_duplicate=True),
    Input({'type': 'delete_citation', 'index': ALL}, 'n_clicks'),
    State("project_name", "data"),
    prevent_initial_call=True
)
def delete_citation(btn, project_name):
    if ctx.triggered_id['type'] == 'delete_citation' and any(item is not None for item in btn):
        connection = get_connection()
        project = connection.get_project(project_name)
        project.delete_citation(ctx.triggered_id['index'])
        project_json = json.dumps(project.to_dict())
        return get_citations(project_json)
    else:
        raise PreventUpdate


@callback(
    Output('directory_table', 'children'),
    Input('filter_directory_tags_btn', 'n_clicks'),
    Input('filter_directory_tags', 'value'),
    State('project_store', 'data'),
    prevent_initial_call=True)
def filter_directory_table(btn, filter, project):
    # Apply filter to the directories table
    if ctx.triggered_id == 'filter_directory_tags_btn' or filter:
        if filter or filter == "":
            try:
                return get_directories_table(project, filter)
            except (FailedConnectionException, UnsuccessfulGetException) as err:
                return dbc.Alert(str(err), color="danger")
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate


@callback(
    Output("download_project", "data"),
    Input("btn_download_project", "n_clicks"),
    State("project_name", "data"),
    prevent_initial_call=True
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

            initial_project_data = json.dumps(project.to_dict())
            initial_directory_list_data = json.dumps([d.to_dict() for d in project.get_all_directories()])
        
        except (FailedConnectionException, UnsuccessfulGetException) as err:
            return dbc.Alert(str(err), color="danger")
        
        # Only show project contents if the user possesses rights (necessary because otherwise users that are not assigned rights, see everything!)
        if project.your_user_role in ["Owners","Members", "Collaborators"]:
            return html.Div([
                dcc.Store(id='project_store', data=initial_project_data),
                dcc.Store(id='dirlist_store', data=initial_directory_list_data),
                dcc.Store(id='project_name', data=project.name),

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
                            ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
                ], className="mb-3"),

                # Project Information (owners,..)
                dbc.Card([
                    dbc.CardHeader(
                        children=[
                            html.H4("Details"),
                            html.Div([
                                modal_edit_project(project),
                                modal_add_user_to_project(project,connection.all_users)], className="d-grid gap-2 d-md-flex justify-content-md-end")
                           ],
                        className="d-flex justify-content-between align-items-center"),
                    dcc.Loading(dbc.CardBody(get_details(initial_project_data), id="details_card"), color=colors['sage'])], class_name="custom-card mb-3"),
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
                        dcc.Loading(html.Div(get_directories_table(
                            initial_directory_list_data), id='directory_table'), color=colors['sage']),
                    ])], class_name="custom-card mb-3"),
                dbc.Card([
                    dbc.CardHeader([
                        html.H4("Sources"),
                        modal_add_citation(project)],
                        className="d-flex justify-content-between align-items-center"),
                    dbc.CardBody([
                        dcc.Loading(html.Div(get_citations(
                            initial_project_data), id='citation_table'), color=colors['sage'])
                    ])
                ], class_name="custom-card mb-3"),
                html.Div([
                    modal_delete(project),
                    modal_delete_data(project)], style={'float': 'right'}, className="mt-3 mb-5 d-grid gap-2 d-md-flex justify-content-md-end"),
            ])
        else:
            return dbc.Alert(f"Security warning: no access rights. If you wish to access this data, please contact: {', '.join(str(i) for i in project.owners )}.", color="warning")
    else:
        return dbc.Alert("No Project found.", color="danger")
