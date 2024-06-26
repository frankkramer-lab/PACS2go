import json
import dash_bootstrap_components as dbc
from dash import (Input, Output, State, callback, ctx, dcc, html, no_update,
                  register_page)
from dash.exceptions import PreventUpdate
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulAttributeUpdateException,
    UnsuccessfulCreationException, UnsuccessfulGetException)
from pacs2go.frontend.helpers import (colors, get_connection,
                                      login_required_interface)

register_page(__name__, title='Projects - PACS2go', path='/projects')


def get_projects_table(projects_json_data: dict, filter: str = ''):
    try:
        rows = []
        projects = json.loads(projects_json_data)


        for p in projects:
            keywords = p['keywords'] if p['keywords'] else "-"
            # Only show rows if no filter is applied of if the filter has a match in the project's keywords
            if filter.lower() in keywords or filter.lower() in p['name'] or len(filter) == 0:
                # Project names represent links to individual project pages
                rows.append(html.Tr([html.Td(dcc.Link(p['name'], href=f"/project/{p['name']}", className="fw-bold text-decoration-none", style={'color': colors['links']})), html.Td(
                    p['your_user_role'].capitalize()), html.Td(p['number_of_directories']), html.Td(p['keywords']), html.Td(p['timestamp_creation']), html.Td(p['last_updated'])]))
    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return dbc.Alert(str(err), color="danger")

    table_header = [
        html.Thead(
            html.Tr([html.Th("Project Name"), html.Th("Your user role"), html.Th("Number of Directories"), html.Th("Keywords"),  html.Th("Created on"),  html.Th("Last Updated on")]))
    ]

    table_body = [html.Tbody(rows)]

    # Put together project table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True, responsive=True)
    return table


def modal_create():
    # Modal view for project creation
    return html.Div([
        # Button which triggers modal activation
        dbc.Button([html.I(className="bi bi-plus-circle me-2"),
                    "Create new Project"], id="create_project", size="md", color="success"),
        # Actual modal view
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Create New Project")),
                dbc.ModalBody([
                    html.Div(id='create-project-content'),
                    dbc.Label(
                        "Please enter a unique name for your project. (Avoid ä,ö,ü and ß)"),
                    # Input Text Field for project name
                    dbc.Input(id="project_name",
                              placeholder="Project Name...", required=True),
                    dbc.Label(
                        "Please enter a description for your project.", class_name="mt-2"),
                    # Input Text Field for project description
                    dbc.Input(id="project_description",
                              placeholder="This project is used to..."),
                    dbc.Label(
                        "Please enter searchable keywords. Each word, separated by a space, can be individually used as a search string.", class_name="mt-2"),
                    # Input Text Field for project keywords
                    dbc.Input(id="project_keywords",
                              placeholder="Dermatology Skin Cancer...."),
                    dbc.Label(
                        "Please enter desired parameters.", class_name="mt-2"),
                    # Input Text Field for project parameters
                    dbc.Textarea(id="project_parameters",
                              placeholder="..."),
                ]),
                dbc.ModalFooter([
                    # Button which triggers the creation of a project (see modal_and_project_creation)
                    dbc.Button("Create Project",
                               id="create_and_close", color="success"),
                    # Button which causes modal to close/disappear
                    dbc.Button("Close", id="close_modal_create", outline=True, color="success",)
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
     Output('create-project-content', 'children'),
     Output('projects_table', 'children', allow_duplicate=True),],
    [Input('create_project', 'n_clicks'),
     Input('close_modal_create', 'n_clicks'),
     Input('create_and_close', 'n_clicks')],
    State("modal_create", "is_open"),
    State('project_name', 'value'),
    State('project_description', 'value'),
    State('project_keywords', 'value'),
    State('project_parameters', 'value'),
    prevent_initial_call=True)
def modal_and_project_creation(open, close, create_and_close, is_open, project_name, description, keywords, parameters):
    # Open/close modal via button click
    if ctx.triggered_id == "create_project" or ctx.triggered_id == "close_modal_create":
        return not is_open, no_update, no_update

    # User tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "create_and_close" and project_name is None:
        return is_open, dbc.Alert("Please specify project name.", color="danger"), no_update

    # User does everything "right" for project creation
    elif ctx.triggered_id == "create_and_close" and project_name is not None:
        # Project name cannot contain whitespaces
        project_name = str(project_name).replace(" ", "_")
        try:
            connection = get_connection()
            keywords if keywords else "No keywords."
            description if description else "No description."
            parameters if parameters else "No parameters."
            # Try to create project
            project = connection.create_project(
                name=project_name, description=description, keywords=keywords, parameters=parameters)
            projects = json.dumps([p.to_dict() for p in connection.get_all_projects(only_accessible=True)])
            return is_open, dbc.Alert([html.Span("A new project has been successfully created! "),
                                       html.Span(dcc.Link(f" Click here to go to the new project {project.name}.",
                                                          href=f"/project/{project.name}",
                                                          className="fw-bold text-decoration-none",
                                                          style={'color': colors['links']}))], color="success"), get_projects_table(projects)

        except (FailedConnectionException, UnsuccessfulGetException, UnsuccessfulAttributeUpdateException, UnsuccessfulCreationException) as err:
            return is_open, dbc.Alert(str(err), color="danger"), no_update

    else:
        raise PreventUpdate


@callback(
    Output('projects_table', 'children', allow_duplicate=True),
    Input('filter_project_keywords_btn', 'n_clicks'),
    Input('filter_project_keywords', 'value'),
    State('projects_list_store', 'data'),
    prevent_initial_call=True)
def filter_projects_table(btn, filter, projects):
    # Apply filter to the projects table
    if ctx.triggered_id == 'filter_project_keywords_btn' or filter:
        return get_projects_table(projects, filter)
    else:
        raise PreventUpdate
    
@callback(
    Output("dymanic_search_projects", "options"),
    Input("dymanic_search_projects", "search_value"),
    State("no_access_project_names_store","data"),
)
def update_project_search_options(search_value, projects_json):

    if not search_value:
        raise PreventUpdate
    
    projects = json.loads(projects_json)
    return [{'label': dcc.Link(project['name'] + ", Owner(s) of this project: " + ', '.join(project['owners']), href=f"/project/{project['name']}",
                                className="text-decoration-none",style={'color': colors['links']}),'value': project['name']} 
                                for project in projects if search_value.lower() in project['name'].lower()]

#################
#  Page Layout  #
#################

def layout():
    if not current_user.is_authenticated:
        return login_required_interface()
    else:
        connection = get_connection()
        # Retrieve all projects to which the user has any rights
        if current_user.id != 'admin':
            initial_projects_data = json.dumps([p.to_dict() for p in connection.get_all_projects(only_accessible=True)])
        else:
            initial_projects_data = json.dumps([p.to_dict() for p in connection.get_all_projects()])
        

        # Retrieve all projects to which the user has no rights
        no_access_projects = json.dumps([p.to_dict() for p in connection.get_all_projects() if p.your_user_role == ''])

        return html.Div(
            children=[
                dcc.Store(id='projects_list_store', data=initial_projects_data),
                dcc.Store(id='no_access_project_names_store', data=no_access_projects),
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
                                "Filter", id="filter_project_keywords_btn", outline=True, color="secondary"))
                        ], class_name="mb-3"),

                        dcc.Loading(
                            html.Div(get_projects_table(initial_projects_data), id='projects_table'), color=colors['sage']),
                    ])], class_name="custom-card mb-3"),
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Discover New Projects"),
                        dcc.Dropdown(id="dymanic_search_projects", placeholder="Type to search available projects..."),
                ])], class_name="custom-card mb-3"),

            ])
