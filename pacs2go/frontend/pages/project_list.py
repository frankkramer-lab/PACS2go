from pacs2go.data_interface.exceptions.exceptions import FailedConnectionException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulAttributeUpdateException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulGetException
from pacs2go.data_interface.exceptions.exceptions import UnsuccessfulCreationException
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import get_connection
from pacs2go.frontend.helpers import login_required_interface

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
from flask_login import current_user

register_page(__name__, title='Projects - PACS2go', path='/projects')


def get_projects_table(filter: str = ''):
    try:
        # Get list of all project names, specific user roles and number of directories per project
        connection = get_connection()
        rows = []
        projects = connection.get_all_projects()
        for p in projects:
            # Only show rows if no filter is applied of if the filter has a match in the project's keywords
            if filter.lower() in p.keywords.lower() or len(filter) == 0:
                # Project names represent links to individual project pages
                rows.append(html.Tr([html.Td(dcc.Link(p.name, href=f"/project/{p.name}", className="fw-bold text-decoration-none", style={'color': colors['links']})), html.Td(
                    p.your_user_role.capitalize()), html.Td(len(p.get_all_directories())), html.Td(p.keywords)]))
    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return dbc.Alert(str(err), color="danger")

    table_header = [
        html.Thead(
            html.Tr([html.Th("Project Name"), html.Th("Your user role"), html.Th("Number of Directories"), html.Th("Keywords")]))
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
                    dbc.Label(
                        "Please enter a unique name for your project. (Don't use ä,ö,ü or ß)"),
                    # Input Text Field for project name
                    dbc.Input(id="project_name",
                              placeholder="Project Name...", required=True),
                    dbc.Label(
                        "Please enter a description for your project.", class_name="mt-2"),
                    # Input Text Field for project name
                    dbc.Input(id="project_description",
                              placeholder="This project is used to..."),
                    dbc.Label(
                        "Please enter searchable keywords. Each word, separated by a space, can be individually used as a search string.", class_name="mt-2"),
                    # Input Text Field for project name
                    dbc.Input(id="project_keywords",
                              placeholder="Dermatology Skin Cancer...."),
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

# Callback for project creation modal view and executing project creation
@callback(
    [Output('modal_create', 'is_open'),
     Output('create-project-content', 'children')],
    [Input('create_project', 'n_clicks'),
     Input('close_modal_create', 'n_clicks'),
     Input('create_and_close', 'n_clicks')],
    State("modal_create", "is_open"),
    State('project_name', 'value'),
    State('project_description', 'value'),
    State('project_keywords', 'value'),
    prevent_initial_call=True)
def modal_and_project_creation(open, close, create_and_close, is_open, project_name, description, keywords):
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
            connection = get_connection()
            # Try to create project
            project = connection.create_project(
                name=project_name, description=description, keywords=keywords)
            return is_open, dbc.Alert([html.Span("A new project has been successfully created! "),
                                       html.Span(dcc.Link(f" Click here to go to the new project {project.name}.",
                                                          href=f"/project/{project.name}",
                                                          className="fw-bold text-decoration-none",
                                                          style={'color': colors['links']}))], color="success")

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException, UnsuccessfulCreationException) as err:
            return is_open, dbc.Alert(str(err), color="danger")

    else:
        raise PreventUpdate


@callback(
    Output('projects_table', 'children'),
    Input('filter_project_keywords_btn', 'n_clicks'),
    Input('filter_project_keywords', 'value'),
    prevent_initial_call=True)
def filter_projects_table(btn, filter):
    # Apply filter to the projects table
    if ctx.triggered_id == 'filter_project_keywords_btn' or filter:
        return get_projects_table(filter)
    else:
        raise PreventUpdate


#################
#  Page Layout  #
#################

def layout():
    if not current_user.is_authenticated:
        return login_required_interface()

    return html.Div(
        children=[
            # Breadcrumbs
            html.Div(
                [
                    dcc.Link(
                        "Home", href="/", style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span("All Projects", className='active fw-bold', style={"color": "#707070"})],
                className='breadcrumb'),

            # Header including page title and create button
            html.Div([
                html.H1(
                    children='Your Projects'),
                html.Div(modal_create(),
                         className="d-flex justify-content-between")
            ], className="d-flex justify-content-between mb-4"),

            # Project table
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(dbc.Input(id="filter_project_keywords",
                                          placeholder="Search keywords.. (e.g. 'CT')")),
                        dbc.Col(dbc.Button(
                            "Filter", id="filter_project_keywords_btn"))
                    ], class_name="mb-3"),

                    dbc.Spinner(
                        html.Div(get_projects_table(), id='projects_table')),
                ])], class_name="mb-3"),

        ])
