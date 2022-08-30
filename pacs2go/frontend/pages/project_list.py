from dash import html, dcc, callback, Input, Output, register_page, ctx, State, no_update
import dash_bootstrap_components as dbc
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT, XNATProject


register_page(__name__, title='Projects', path='/projects')
server = 'http://xnat-web:8080'

# TODO: only make project clickable if user has rights to certain project


def get_projects():
    # get list of all project names, specific user roles and number of directories per project
    rows = []
    with XNAT(server, "admin", "admin") as connection:
        for p in connection.get_all_projects():
            # project names represent links to individual project pages
            rows.append(html.Tr([html.Td(html.A(p.name, href=f"/project/{p.name}", className="text-dark")), html.Td(
                "You are an " + p.your_user_role + " for this project."), html.Td(len(p.get_all_directories()))]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Project Name"), html.Th("Your user role"), html.Th("Number of Directories")]))
    ]

    table_body = [html.Tbody(rows)]

    # put together project table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table

# modal view for project creation
modal = html.Div(
    [
        # button which triggers modal activation
        dbc.Button([html.I(className="bi bi-plus-circle-dotted me-2"),
                    "Create new Project"], id="create_project", size="lg", color="success"),
        # actual modal view
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Create New Project")),
                dbc.ModalBody([
                    html.Div(id='create-project-content'),
                    dbc.Label("Project"),
                    # Input Text Field for project name
                    dbc.Input(id="project_name", placeholder="Project Name...", required=True),
                ]),
                dbc.ModalFooter([
                    # button which triggers the creation of a project (see modal_and_project_creation)
                    dbc.Button("Create Project", id="create_and_close", color="success"),
                    # button which causes modal to close/disappear
                    dbc.Button("Close", id="close")
                ]),
            ],
            id="modal",
            is_open=False,
        ),
    ]
)


#################
#   Callbacks   #
#################

# callback for project creation modal view and executing project creation
@callback([Output('modal', 'is_open'), Output('create-project-content', 'children')],
          [Input('create_project', 'n_clicks'), Input('close', 'n_clicks'), Input('create_and_close', 'n_clicks')],
          State("modal", "is_open"), State('project_name', 'value'))
def modal_and_project_creation(open, close, create_and_close, is_open, project_name):
    # open/close modal via button click
    if ctx.triggered_id == "create_project" or ctx.triggered_id == "close":
        return not is_open, no_update
    # user tries to create modal without specifying a project name -> show alert feedback
    elif ctx.triggered_id == "create_and_close" and project_name is None:
        return is_open, dbc.Alert("Please specify project name.", color="danger")
    # user does everything "right" for project creation
    elif ctx.triggered_id == "create_and_close" and project_name is not None:
        # project name cannot contain whitespaces
        project_name = str(project_name).replace(" ","_")
        try:
            with XNAT(server,"admin","admin") as connection:
                # try to create project 
                XNATProject(connection, project_name)
        except Exception as err:
            # TODO: differentiate between different exceptions
            return is_open, dbc.Alert(str(err), color="danger")
        return not is_open, no_update
    else:
        return is_open, no_update


#################
#  Page Layout  #
#################

def layout():
    return html.Div(children=[
        html.Div([
            html.Div(html.H1(
                children='Your Projects'), className="p-2"),
            html.Div(modal, className="p-2")
        ], className="d-flex justify-content-between mb-4 "),
        get_projects(),
    ])
