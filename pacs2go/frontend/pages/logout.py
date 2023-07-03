from pacs2go.frontend.helpers import colors

import dash
from dash import dcc
from dash import html
from flask_login import current_user
from flask_login import logout_user

dash.register_page(__name__)


def layout():
    logout_user()
    return html.Div(
        [
            html.Div(
                [html.H2("You have been logged out. - You will be redirected to login.."), html.H4(dcc.Link('Or click here.', href='/login', className="fw-bold text-decoration-none",
                                                                                                            style={'color': colors['links']}))]),
            dcc.Interval(id={'index': 'redirectLogin',
                         'type': 'redirect'}, n_intervals=0, interval=1*3000)
        ], style={
            'display': 'flex',
            'justify-content': 'center',
            'align-items': 'center',
            'height': '80vh'
        },
    )
