import os

import dash_bootstrap_components as dbc
from dash import ALL
from dash import Dash
from dash import dcc
from dash import html
from dash import Input
from dash import no_update
from dash import Output
from dash import page_container
from dash import page_registry
from flask import Flask
from flask import redirect
from flask import request
from flask import session
from flask_login import current_user
from flask_login import login_user
from flask_login import LoginManager
from flask_login import logout_user
from flask_login import UserMixin

from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import restricted_page

# Flask Login based on https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507
# Exposing the Flask Server to enable configuring it for logging in
server = Flask(__name__)


@server.route('/login', methods=['POST'])
def login_button_click():
    if request.form:
        username = request.form['username']
        password = request.form['password']
        if VALID_USERNAME_PASSWORD.get(username) is None:
            return """invalid username and/or password <a href='/login'>login here</a>"""
        if VALID_USERNAME_PASSWORD.get(username) == password:
            login_user(User(username))
            if 'url' in session:
                if session['url']:
                    url = session['url']
                    session['url'] = None
                    return redirect(url)  # redirect to target url
            return redirect('/')  # redirect to home
        return """invalid username and/or password <a href='/login'>login here</a>"""


app = Dash(name="xnat2go", pages_folder="/pacs2go/frontend/pages", use_pages=True, server=server,
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)

# Keep this out of source code repository - save in a file or a database
#  passwords should be encrypted
VALID_USERNAME_PASSWORD = {"admin": "admin", "test": "test"}


# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


class User(UserMixin):
    # User data model. It has to have at least self.id as a minimum
    def __init__(self, username):
        self.id = username


@login_manager.user_loader
def load_user(username):
    """This function loads the user by user id. Typically this looks up the user from a user database.
    We won't be registering or looking up users in this example, since we'll just login using LDAP server.
    So we'll simply return a User object with the passed in username.
    """
    return User(username)


app.layout = html.Div(
    [
        # navigation bar on top
        dcc.Location(id="url"),
        html.Div(id="user-status-header"),
        dbc.NavbarSimple(
            children=[
                dbc.NavLink(
                    "Home", href=page_registry['pacs2go.frontend.pages.home']['path']),
                dbc.NavLink(
                    "Projects", href=page_registry['pacs2go.frontend.pages.project_list']['path'], className="fw-lighter"),
                dbc.NavLink(
                    "Upload", href=page_registry['pacs2go.frontend.pages.large_upload']['path'], className="fw-lighter"),
            ],
            brand="PACS2go",
            brand_href="/",
            color=colors['sage'],
            className="fw-bold mb-3",
            dark=True,
        ),
        # placeholder for each registered page (see pages folder)
        html.Div([page_container], style={'padding': '1% 11%'})
    ]
)


@app.callback(
    Output("user-status-header", "children"),
    Output('url', 'pathname'),
    Input("url", "pathname"),
    Input({'index': ALL, 'type': 'redirect'}, 'n_intervals')
)
def update_authentication_status(path, n):
    # logout redirect
    if n:
        if not n[0]:
            return '', no_update
        else:
            return '', '/login'

    # test if user is logged in
    if current_user.is_authenticated:
        if path == '/login':
            return dcc.Link("logout", href="/logout"), '/'
        return dcc.Link("logout", href="/logout"), no_update
    else:
        # if page is restricted, redirect to login and save path
        if path in restricted_page:
            session['url'] = path
            return dcc.Link("login", href="/login"), '/login'

    # if path not login and logout display login link
    if current_user and path not in ['/login', '/logout']:
        return dcc.Link("login", href="/login"), no_update

    # if path login and logout hide links
    if path in ['/login', '/logout']:
        return '', no_update


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, dev_tools_hot_reload=False)
