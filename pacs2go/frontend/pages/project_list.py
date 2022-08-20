from dash import html, dcc, callback, Input, Output, register_page, page_registry
import dash_bootstrap_components as dbc
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT


register_page(__name__, title='Projects', path='/projects')
server = 'http://xnat-web:8080'


def get_projects():
    # get list of all project names, specific user roles and number of directories per project
    rows = []
    with XNAT(server, "admin", "admin") as connection:
        for p in connection.get_all_projects():
            rows.append(html.Tr([html.Td(html.A(p.name, href=f"/project/{p.name}", className="text-dark")), html.Td(
                "You are an " + p.your_user_role + " for this project."),html.Td(len(p.get_all_directories()))]))

    table_header = [
        html.Thead(
            html.Tr([html.Th("Project Name"), html.Th("Your user role"), html.Th("Number of Directories")]))
    ]

    table_body = [html.Tbody(rows)]

    # put together project table
    table = dbc.Table(table_header + table_body,
                      striped=True, bordered=True, hover=True)
    return table


def layout():
    return html.Div(children=[html.H1(
    children='Your Projects',
    style={'textAlign': 'left', }, className="pb-3"),
    get_projects()
])
