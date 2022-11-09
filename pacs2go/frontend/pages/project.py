from typing import Optional
from dash import html, callback, Input, Output, register_page, ctx, State, no_update, dcc
from pacs2go.data_interface.pacs_data_interface import Project
import dash_bootstrap_components as dbc
from pacs2go.frontend.helpers import get_connection, colors

register_page(__name__, title='Project - PACS2go',
              path_template='/project/<project_name>')


def get_details(project: Project):
    description = "Description: " + project.description
    owners = "Owners: " + ', '.join(project.owners)
    return html.Div([html.H5(owners), html.H5(description)])


def get_directories(project: Project):
    # get list of all directory names and number of files per directory
    rows = []
    for d in project.get_all_directories():
        # directory names represent links to individual directory pages
        rows.append(html.Tr([html.Td(dcc.Link(d.name, href=f"/dir/{project.name}/{d.name}", className="text-decoration-none", style={'color': colors['links']})), html.Td(
            len(d.get_all_files()))]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Directory Name"), html.Th("Number of Files")]))
    ]

    table_body = [html.Tbody(rows)]

    # put together directory table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return html.Div([html.H5("Directories:"), table])


def modal_delete(project: Project):
    # modal view for project deletion
    return html.Div([
        # button which triggers modal activation
        dbc.Button([html.I(className="bi bi-trash me-2"),
                    "Delete Project"], id="delete_project", size="md", color="danger"),
        # actual modal view
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
                    # button which triggers the deletion of a project (see modal_and_project_creation)
                    dbc.Button("Delete Project",
                               id="delete_and_close", color="danger"),
                    # button which causes modal to close/disappear
                    dbc.Button("Close", id="close_modal_delete"),
                ]),
            ],
            id="modal_delete",
            is_open=False,
        ),
    ])


def modal_delete_data(project: Project):
    # modal view for deleting all directories of a project
    return html.Div([
        # button which triggers modal activation
        dbc.Button([html.I(className="bi bi-trash me-2"),
                    "Delete All Directories"], id="delete_project_data", size="md", color="danger"),
        # actual modal view
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
                    # button which triggers the directory deletion (see modal_and_project_creation)
                    dbc.Button("Delete All Directories",
                               id="delete_data_and_close", color="danger"),
                    # button which causes modal to close/disappear
                    dbc.Button("Close", id="close_modal_delete_data"),
                ]),
            ],
            id="modal_delete_data",
            is_open=False,
        ),
    ])


def insert_data(project: Project):
    return html.Div(dbc.Button([html.I(className="bi bi-cloud-upload me-2"),
                    "Insert Data"], href=f"/upload/{project.name}", size="md", color="success"))


#################
#   Callbacks   #
#################

# callback for project deletion modal view and executing project deletion
@callback([Output('modal_delete', 'is_open'), Output('delete-project-content', 'children')],
          [Input('delete_project', 'n_clicks'), Input(
              'close_modal_delete', 'n_clicks'), Input('delete_and_close', 'n_clicks')],
          State("modal_delete", "is_open"), State("project", "value"))
def modal_and_project_deletion(open, close, delete_and_close, is_open, project_name):
    # open/close modal via button click
    if ctx.triggered_id == "delete_project" or ctx.triggered_id == "close_modal_delete":
        return not is_open, no_update
    if ctx.triggered_id == "delete_and_close":
        try:
            with get_connection() as connection:
                project = connection.get_project(project_name)
                if project:
                    project.delete_project()
                # redirect to project list after deletion
                return not is_open, dcc.Location(href=f"/projects/", id="redirect_after_project_delete")
        except Exception as err:
            return is_open, dbc.Alert("Can't be deleted " + str(err), color="danger")
    else:
        return is_open, no_update


# callback used to delete all directories of a project (open modal view + actual deletion)
@callback([Output('modal_delete_data', 'is_open'), Output('delete-project-data-content', 'children')],
          [Input('delete_project_data', 'n_clicks'), Input(
              'close_modal_delete_data', 'n_clicks'), Input('delete_data_and_close', 'n_clicks')],
          State("modal_delete_data", "is_open"), State("project_2", "value"))
def modal_and_project_data_deletion(open, close, delete_data_and_close, is_open, project_name):
    # open/close modal via button click
    if ctx.triggered_id == "delete_project_data" or ctx.triggered_id == "close_modal_delete_data":
        return not is_open, no_update
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


#################
#  Page Layout  #
#################

def layout(project_name: Optional[str]=None):
    try:
        if project_name:
            with get_connection() as connection:
                project = connection.get_project(project_name)
                if project:
                    return html.Div([
                        dbc.Row([
                            dbc.Col(html.H1(f"Project {project.name}", style={
                                    'textAlign': 'left', })),
                            dbc.Col(
                                [insert_data(project),
                                modal_delete(project),
                                modal_delete_data(project), ], className="d-grid gap-2 d-md-flex justify-content-md-end"),
                        ], className="mb-3"),
                        get_details(project),
                        get_directories(project)
                    ])
                else:
                    return dbc.Alert("No Project found.", color="danger")
    except:
        return dbc.Alert("No Project found.", color="danger")
