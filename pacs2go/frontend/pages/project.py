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
from dash.exceptions import PreventUpdate

from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection

register_page(__name__, title='Project - PACS2go',
              path_template='/project/<project_name>')


def get_details(project: Project):
    description = "Description: " + project.description
    keywords = "Keywords: " + project.keywords
    owners = "Owners: " + ', '.join(project.owners)
    return [html.H6(owners), html.H6(description), html.H6(keywords)]


def get_directories_table(project: Project, filter: str = ''):
    # Get list of all directory names and number of files per directory
    rows = []
    for d in project.get_all_directories():
        if filter.lower() in d.contained_file_tags.lower() or len(filter) == 0:
            # Directory names represent links to individual directory pages
            rows.append(html.Tr([html.Td(dcc.Link(d.name, href=f"/dir/{project.name}/{d.name}", className="text-decoration-none", style={'color': colors['links']})), html.Td(
                d.number_of_files), html.Td(d.contained_file_tags)]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Directory Name"), html.Th("Number of Files"), html.Th("Contained File Tags in this Directory")]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together directory table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def modal_delete(project: Project):
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
                    dbc.Input(id="project", value=project.name, disabled=True),
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
    # Modal view for project deletion
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
                ]),
                dbc.ModalFooter([
                    # Button which triggers the creation of a project (see modal_and_project_creation)
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


def insert_data(project: Project):
    # Link to Upload functionality with a set project name
    return html.Div(dbc.Button([html.I(className="bi bi-cloud-upload me-2"),
                    "Insert Data"], href=f"/upload/{project.name}", size="md", color="success"))


#################
#   Callbacks   #
#################

@callback([Output('modal_delete', 'is_open'), Output('delete-project-content', 'children')],
          [Input('delete_project', 'n_clicks'),
           Input('close_modal_delete', 'n_clicks'),
           Input('delete_and_close', 'n_clicks')],
          State("modal_delete", "is_open"),
          State("project", "value"))
# Callback for project deletion modal view and executing project deletion
def modal_and_project_deletion(open, close, delete_and_close, is_open, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "delete_project" or ctx.triggered_id == "close_modal_delete":
        return not is_open, no_update

    if ctx.triggered_id == "delete_and_close":
        try:
            with get_connection() as connection:
                project = connection.get_project(project_name)

                if project:
                    project.delete_project()

                # Redirect to project list after deletion
                return not is_open, dcc.Location(href=f"/projects/", id="redirect_after_project_delete")

        except Exception as err:
            return is_open, dbc.Alert("Can't be deleted " + str(err), color="danger")
    else:
        return is_open, no_update


@callback([Output('modal_delete_data', 'is_open'), Output('delete-project-data-content', 'children')],
          [Input('delete_project_data', 'n_clicks'),
           Input('close_modal_delete_data', 'n_clicks'),
           Input('delete_data_and_close', 'n_clicks')],
          State("modal_delete_data", "is_open"),
          State("project_2", "value"))
# Callback used to delete all directories of a project (open modal view + actual deletion)
def modal_and_project_data_deletion(open, close, delete_data_and_close, is_open, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "delete_project_data" or ctx.triggered_id == "close_modal_delete_data":
        return not is_open, no_update

    # Delete Button in Modal View
    if ctx.triggered_id == "delete_data_and_close":
        try:
            with get_connection() as connection:
                project = connection.get_project(project_name)
                if project:
                    dirs = project.get_all_directories()
                    if len(dirs) == 0:
                        return is_open,  dbc.Alert("Project is empty", color="danger")
                    else:
                        for d in dirs:
                            d.delete_directory()
                        return not is_open, no_update

        except Exception as err:
            return is_open, dbc.Alert("Can't be deleted " + str(err), color="danger")

    else:
        return is_open, no_update


@callback([Output('modal_edit_project', 'is_open'), Output('edit-project-content', 'children'), Output('details_card','children')],
          [Input('edit_project', 'n_clicks'),
           Input('close_modal_edit', 'n_clicks'),
           Input('edit_and_close', 'n_clicks')],
          State("modal_edit_project", "is_open"),
          State('project_store', 'data'),
          State('new_project_description', 'value'),
          State('new_project_keywords', 'value'))
# Callback used to edit project description and keywords
def modal_edit_project_callback(open, close, edit_and_close, is_open, project_name, description, keywords):
    # Open/close modal via button click
    if ctx.triggered_id == "edit_project" or ctx.triggered_id == "close_modal_edit":
        return not is_open, no_update, no_update
    # User does everything "right"
    elif ctx.triggered_id == "edit_and_close":
        try:
            with get_connection() as connection:
                project = connection.get_project(project_name)
                if description:
                    # Set new description
                    project.set_description(description)
                if keywords:
                    # Set new keywords
                    project.set_keywords(keywords)
                return not is_open, no_update, get_details(project)
        except Exception as err:
            # TODO: differentiate between different exceptions
            return is_open, dbc.Alert(str(err), color="danger"), no_update
    else:
        raise PreventUpdate


@callback(Output('directory_table', 'children'),
          Input('filter_directory_tags_btn', 'n_clicks'),
          State('filter_directory_tags', 'value'),
          State('project_store', 'data'))
def filter_files_table(btn, filter, project_name):
    # Apply filter to the directories table
    if ctx.triggered_id == 'filter_directory_tags_btn':
        if filter or filter == "":
            with get_connection() as connection:
                return get_directories_table(connection.get_project(project_name), filter)
        else:
            raise PreventUpdate
    else:
        raise PreventUpdate


#################
#  Page Layout  #
#################

def layout(project_name: Optional[str] = None):
    try:
        if project_name:
            with get_connection() as connection:
                project = connection.get_project(project_name)

                if project:
                    return html.Div([
                        dcc.Store(id='project_store', data=project.name),
                        # Header including page title and action buttons
                        dbc.Row([
                            dbc.Col(html.H1(f"Project {project.name}", style={
                                    'textAlign': 'left', })),
                            dbc.Col(
                                [insert_data(project),
                                 modal_edit_project(project),
                                 modal_delete(project),
                                 modal_delete_data(project), ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
                        ], className="mb-3"),
                        # Project Information (owners,..)
                        dbc.Card([
                            dbc.CardHeader("Details"),
                            dbc.CardBody(get_details(project), id="details_card")], class_name="mb-3"),
                        dbc.Card([
                            dbc.CardHeader('Directories'),
                            dbc.CardBody([
                                # Filter file tags
                                dbc.Row([
                                    dbc.Col(dbc.Input(id="filter_directory_tags",
                                        placeholder="Search keywords.. (e.g. 'CT')")),
                                    dbc.Col(dbc.Button(
                                        "Filter", id="filter_directory_tags_btn"))
                                ], class_name="mb-3"),
                                # Directories Table
                                html.Div(get_directories_table(
                                    project), id='directory_table'),
                            ])], class_name="mb-3"),

                    ])

                else:
                    return dbc.Alert("No Project found.", color="danger")

    except Exception as err:
        return dbc.Alert(f"No Project found. + {err}", color="danger")
