from typing import List

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

from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection


register_page(__name__, title='Projects - PACS2go', path='/projects')

# TODO: only make project clickable if user has rights to certain project


def get_projects_list() -> List[Project]:
    try:
        with get_connection() as connection:
            return connection.get_all_projects()
    except:
        return []


def get_projects_table():
    # Get list of all project names, specific user roles and number of directories per project
    rows = []
    for p in get_projects_list():
        # Project names represent links to individual project pages
        rows.append(html.Tr([html.Td(dcc.Link(p.name, href=f"/project/{p.name}", className="fw-bold text-decoration-none", style={'color': colors['links']})), html.Td(
            p.your_user_role.capitalize()), html.Td(len(p.get_all_directories()))]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Project Name"), html.Th("Your user role"), html.Th("Number of Directories")]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together project table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def modal_create():
    # Modal view for project creation
    return html.Div([
        # Button which triggers modal activation
        dbc.Button([html.I(className="bi bi-plus-circle-dotted me-2"),
                    "Create new Project"], id="create_project", size="lg", color="success"),
        # Actual modal view
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Create New Project")),
                dbc.ModalBody([
                    html.Div(id='create-project-content'),
                    dbc.Label("Please enter a unique name for your project."),
                    # Input Text Field for project name
                    dbc.Input(id="project_name",
                              placeholder="Project Name...", required=True),
                ]),
                dbc.ModalFooter([
                    # Button which triggers the creation of a project (see modal_and_project_creation)
                    dbc.Button("Create Project",
                               id="create_and_close", color="success"),
                    # Button which causes modal to close/disappear
                    dbc.Button("Close", id="close_modal_create")
                ]),
            ],
            id="modal_create",
            is_open=False,
        ),
    ])


#################
#   Callbacks   #
#################

# callback for project creation modal view and executing project creation
@callback([Output('modal_create', 'is_open'), Output('create-project-content', 'children')],
          [Input('create_project', 'n_clicks'), Input(
              'close_modal_create', 'n_clicks'), Input('create_and_close', 'n_clicks')],
          State("modal_create", "is_open"), State('project_name', 'value'))
def modal_and_project_creation(open, close, create_and_close, is_open, project_name):
    # Open/close modal via button click
    if ctx.triggered_id == "create_project" or ctx.triggered_id == "close_modal_create":
        return not is_open, no_update
    # User tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "create_and_close" and project_name is None:
        return is_open, dbc.Alert("Please specify project name.", color="danger")
    # User does everything "right" for project creation
    elif ctx.triggered_id == "create_and_close" and project_name is not None:
        # Project name cannot contain whitespaces
        project_name = str(project_name).replace(" ", "_")
        try:
            with get_connection() as connection:
                # Try to create project
                Project(connection, project_name)
                return not is_open, dcc.Location(href=f"/projects/", id="redirect_after_project_creation")
        except Exception as err:
            # TODO: differentiate between different exceptions
            return is_open, dbc.Alert(str(err), color="danger")
    else:
        return is_open, no_update


#################
#  Page Layout  #
#################

def layout():
    return html.Div(children=[
        # Header including page title and create button
        html.Div([
            html.H1(
                children='Your Projects'),
            html.Div(modal_create(), className="d-flex justify-content-between")
        ], className="d-flex justify-content-between mb-4"),
        # Project information table
        get_projects_table(),
    ])
