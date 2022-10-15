from dash import register_page, html
import dash_bootstrap_components as dbc
from pacs2go.data_interface.pacs_data_interface import Project
from pacs2go.frontend.helpers import get_connection, colors

register_page(__name__, title='PACS2go 2.0', path='/')


def card_view_projects():
    with get_connection() as connection:
        try:
            projects = connection.get_all_projects()
            number_of_projects = len(projects)
        except:
            return dbc.Alert("Projects could not be retrieved.")
    project_list = []
    for p in projects:
        project_list.append(dbc.ListGroupItem([html.A(
            p.name, href=f"/project/{p.name}", className="text-decoration-none", style={'color': colors['links']}),
            html.A(html.I(className="bi bi-plus-square me-2"), href=f"/upload/{p.name}", style={'color': colors['links']})], class_name="d-flex justify-content-between"))
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Projects", className="card-title"),
                html.P(f"Your PACS2Go currently contains {number_of_projects} projects.",
                       className="card-subtitle"),
                dbc.ListGroup(project_list,
                              class_name="my-3"
                              ),
                dbc.Button("Go to Project Overview",
                             href=f"/projects/", outline=False, color='success'),
            ]
        ))
    return card


def card_view_upload():
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Upload", className="card-title"),
                html.P(f"Upload Medical Files. Currently we support DICOM, JPEG, Nifti and JSON.",
                       className="card-subtitle"),
                dbc.Button("Upload to PACS2go", href=f"/upload/none", class_name="mt-3", outline=False, color='success'),
            ]
        ),)
    return card


#################
#  Page Layout  #
#################

def layout():
    return [html.H1(
        children='PACS2go 2.0',
        style={
            'textAlign': 'left',
        }),
        html.Div(children='Exchange medical files.', style={
            'textAlign': 'left',
        }),
        dbc.Row([
            dbc.Col(card_view_projects(),),
            dbc.Col(card_view_upload(),),
        ], class_name="my-3")
    ]
