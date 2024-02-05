import dash_bootstrap_components as dbc
from dash import dcc, html, register_page
from flask_login import current_user

from pacs2go.data_interface.exceptions.exceptions import (
    FailedConnectionException, UnsuccessfulGetException)
from pacs2go.frontend.helpers import (colors, get_connection,
                                      login_required_interface)

register_page(__name__, title='PACS2go 2.0', path='/')


def card_view_projects():
    connection = get_connection()
    try:
        projects = connection.get_all_projects()
        number_of_projects = len(projects)

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return dbc.Alert(str(err))

    project_list = []
    # Only show 8 projects on landing page
    limit = 8
    for index, p in enumerate(projects):
        project_list.append(dbc.ListGroupItem([dcc.Link(
            p.name, href=f"/project/{p.name}", className="text-decoration-none", style={'color': colors['links']}),
            dcc.Link(html.I(className="bi bi-cloud-upload me-2"), href=f"/upload/{p.name}",
                     style={'color': colors['links']})], class_name="d-flex justify-content-between"))

        if index == limit:
            break

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
                           href="/projects/", outline=False, color='success'),
            ]
        ), className="custom-card mb-3")

    return card


def card_view_favorites():
    connection = get_connection()
    try:
        favs = connection.get_favorites(current_user.id)

    except (FailedConnectionException, UnsuccessfulGetException) as err:
        return dbc.Alert(str(err))

    fav_list = []
    for index, d in enumerate(favs):
        fav_list.append(dbc.ListGroupItem([dcc.Link(
            f"{d.project.name} /../ {d.display_name}", href=f"/dir/{d.project.name}/{d.unique_name}", className="text-decoration-none", style={'color': colors['links']}),
            ], 
                class_name="d-flex justify-content-between"))

    if len(favs) > 0:
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4(["Your favorite directories  ", html.I(className=f"bi bi-heart-fill", style={'color': colors['favorite']},)], className="card-title"),
                    dbc.ListGroup(fav_list,
                                class_name="my-3"
                                ),
                ]
            ), className="custom-card")
    else:
        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H4("Your favorite directories", className="card-title"),
                    html.P(f"You have not favorited any directories or subdirectories yet. To do so, navigate to a directory and press the heart in the top right hand corner. This allows for faster access.",
                       className="card-subtitle"),
                ]
            ), className="custom-card")

    return card


def card_view_upload():
    card = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Upload", className="card-title"),
                html.P("Upload Medical Files. Currently we support DICOM, NIFTI, JPEG, PNG, TIFF, CSV and JSON.",
                       className="card-subtitle"),
                dbc.Button([html.I(className="bi bi-cloud-upload me-2"), " Upload to PACS2go"],
                           href=f"/upload/none", class_name="mt-3", outline=False, color='success'),
            ]
        ), className="custom-card mb-3")

    return card


#################
#  Page Layout  #
#################

def layout():
    if not current_user.is_authenticated:
        return login_required_interface()

    else:
        return [
            html.H1(f'Welcome to PACS2go, {current_user.id}!'),
            html.Div('Exchange medical files.'),
            dbc.Row([
                dbc.Col(card_view_projects(),),
                dbc.Col([card_view_upload(), card_view_favorites()]),
            ], class_name="my-3")
        ]
