from dash import html, dcc, callback, Input, Output, register_page
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT
import dash_bootstrap_components as dbc

register_page(__name__, title='Projects', path='/projects')
server = 'http://xnat-web:8080'


def get_projects():
    rows = []
    with XNAT(server, "admin", "admin") as connection:
        for p in connection.get_all_projects():
            rows.append(html.Tr([html.Td(p.name), html.Td("You are an " + p.your_user_role + " for this project.")]))

    table_header = [
        html.Thead(html.Tr([html.Th("Project Name"), html.Th("Your user role")]))
    ]

    table_body = [html.Tbody(rows)]

    table = dbc.Table(table_header + table_body, striped=True, bordered=True, hover=True)
    return table


layout = html.Div(children=[html.H1(
    children='Your Projects',
    style={'textAlign': 'left', }, className="pb-3"),
    get_projects()
])