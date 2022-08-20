from dash import html, dcc, callback, Input, Output, register_page, page_registry
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT
import dash_bootstrap_components as dbc

register_page(__name__, title='Project', path_template='/project/<project_name>')
server = 'http://xnat-web:8080'


def layout(project_name=None):
    return html.Div(children=[html.H1(
        children=f"Project {project_name}",
        style={'textAlign': 'left', }, className="pb-3"),
    ])
