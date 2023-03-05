import os
from datetime import timedelta

import dash_bootstrap_components as dbc
import requests
from dash import ALL
from dash import Dash
from dash import dcc
from dash import html
from dash import Input
from dash import no_update
from dash import Output
from dash import page_container
from dash import page_registry
from dash.exceptions import PreventUpdate
from dotenv import load_dotenv
from flask import Flask
from flask import redirect
from flask import request
from flask import session
from flask_login import current_user
from flask_login import login_user
from flask_login import LoginManager
from flask_login import UserMixin

from pacs2go.frontend.helpers import colors
from pacs2go.frontend.helpers import server_url

# Load environment variables from the .env file
load_dotenv()

# Credit: Flask Login based on https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507
# Exposing the Flask Server to enable configuring it for logging in
server = Flask(__name__)

# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))
server.config['REMEMBER_COOKIE_DURATION'] = timedelta(minutes=10)

# Dash App
app = Dash(name="xnat2go", pages_folder="/pacs2go/frontend/pages", use_pages=True, server=server,
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)

#################
#     Login     #
#################

# Login manager object will be used to login / logout users
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "/login"


class User(UserMixin):
    def __init__(self, username, session_id):
        self.id = username
        self.session_id = session_id

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


class XNATAuthBackend:
    def authenticate(self, username, password):
        # Send request to XNAT server to authenticate user
        data = {"username": username, "password": password}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = requests.post(
            server_url + "/data/services/auth", data=data, headers=headers)
        if response.status_code == 200:
            # Login was successful
            session_id = response.text
            return User(username, session_id)
        else:
            # Login failed
            return None

    def get_user(self, username):
        # Check if user is logged in
        session_id = session.get("session_id")
        if session_id is not None:
            # User is logged in, return user object
            return User(username, session_id)
        else:
            # User is not logged in
            return None


server.config["AUTH_TYPE"] = "XNAT"
# TODO: production: https://flask-login.readthedocs.io/en/latest/#session-protection set to "strong"
login_manager.session_protection = None
login_manager.auth_backend = XNATAuthBackend()


@server.before_request
def make_session_permanent():
    session.permanent = True
    # Defualt permanent_session_lifetime is 31days
    server.permanent_session_lifetime = timedelta(minutes=10)


@server.route('/login', methods=['POST'])
@server.route('/login/', methods=['POST'])
def login_button_click():
    if request.form:
        username = request.form['username']
        password = request.form['password']
        # Authenication via XNATAuthBackend
        user = login_manager.auth_backend.authenticate(username, password)
        if user is not None:
            session["session_id"] = user.session_id
            login_user(user)
            if 'url' in session:
                # Redirect to url that user tried to access before auth
                if session['url']:
                    url = session['url']
                    session['url'] = None
                    return redirect(url)  # Redirect to target url
            return redirect('/')  # Redirect to home
        else:
            return redirect('/login/')
    else:
        redirect('/login')


@login_manager.user_loader
def load_user(username):
    return login_manager.auth_backend.get_user(username)


#################
#   App Layout  #
#################

app.layout = html.Div(
    [
        # navigation bar on top
        dcc.Location(id="url"),
        dbc.NavbarSimple(
            children=[
                dbc.NavLink(
                    "Home", href=page_registry['pacs2go.frontend.pages.home']['path']),
                dbc.NavLink(
                    "Projects", href=page_registry['pacs2go.frontend.pages.project_list']['path'], className="fw-lighter"),
                dbc.NavLink(
                    "Upload", href=page_registry['pacs2go.frontend.pages.large_upload']['path'], className="fw-lighter"),
                html.Div(id="user-status-header"),
            ],
            brand="PACS2go",
            brand_href="/",
            color=colors['sage'],
            className="fw-bold mb-3",
            dark=True,
            fluid=True,
            brand_style={'padding-left': '1%'},
            style={'padding-right': '1%'}
        ),
        # placeholder for each registered page (see pages folder)
        html.Div([page_container], style={'padding': '1% 10%'})
    ]
)


#################
#   Callbacks   #
#################

@app.callback(
    Output("user-status-header", "children"),
    Output('url', 'pathname'),
    Input("url", "pathname"),
    Input({'index': ALL, 'type': 'redirect'}, 'n_intervals')
)
def update_authentication_status(path, n):
    # Logout redirect
    if n:
        if not n[0]:
            return '', no_update
        else:
            return '', '/login'

    # Test if user is logged in
    if current_user.is_authenticated:
        if path == '/login' or path == '/login/':
            return dcc.Link("logout", href="/logout"), '/'
        return dbc.NavLink("Logout", href="/logout"), no_update
    elif current_user and path not in ['/login', '/logout']:
        # If path not login and logout display login link
        # And store path to be redirected to after auth
        session['url'] = path
        return dbc.NavLink("Login", href="/login"), no_update

    # If path login and logout hide links
    if path in ['/login', '/logout', '/login/']:
        return '', no_update


@app.callback(Output("output-state", "children"), Input("url", "pathname"))
def login_feedback(path):
    if path == '/login/':
        return dbc.Alert("Wrong username or password.", color="danger")
    else:
        raise PreventUpdate


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, dev_tools_hot_reload=False)
