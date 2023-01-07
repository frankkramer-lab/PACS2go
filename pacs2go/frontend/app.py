import os
import requests

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
from pacs2go.frontend.helpers import server_url

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Credit: Flask Login based on https://community.plotly.com/t/dash-app-pages-with-flask-login-flow-using-flask/69507
# Exposing the Flask Server to enable configuring it for logging in
server = Flask(__name__)

# Updating the Flask Server configuration with Secret Key to encrypt the user session cookie
server.config.update(SECRET_KEY=os.getenv("SECRET_KEY"))

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
        # Send request to XNAT server to check if user is authenticated https://wiki.xnat.org/display/XAPI/User+Management+API
        response = requests.get(server_url + "/xapi/users/" + self.id)
        if response.status_code == 200:
            # User was found, return True
            return True
        else:
            # User not found, return False
            return False

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
login_manager.session_protection = "strong"
login_manager.auth_backend = XNATAuthBackend()


@server.route('/login', methods=['POST'])
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
                if session['url']:
                    url = session['url']
                    session['url'] = None
                    return redirect(url)  # Redirect to target url
            return redirect('/')  # Redirect to home
        else:
            return redirect('/login')
    else:
        redirect('/login')


@login_manager.user_loader
def load_user(username):
    # Called when flask_login's 'current_user' is used
    session_id = session.get("session_id")
    user = User(username, session_id)
    # Check if user is authenticated, if yes return user otherwise 'None' must be returned
    if user.is_authenticated:
        return user
    else:
        return None


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
        ),
        # placeholder for each registered page (see pages folder)
        html.Div([page_container], style={'padding': '1% 11%'})
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
        if path == '/login':
            return dcc.Link("logout", href="/logout"), '/'
        return dbc.NavLink("Logout", href="/logout"), no_update
    else:
        # If page is restricted, redirect to login and save path
        if path in restricted_page:
            session['url'] = path
            return dbc.NavLink("Login", href="/login"), '/login'

    # If path not login and logout display login link
    if current_user and path not in ['/login', '/logout']:
        return dbc.NavLink("Login", href="/login"), no_update

    # If path login and logout hide links
    if path in ['/login', '/logout']:
        return '', no_update


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, dev_tools_hot_reload=False)
