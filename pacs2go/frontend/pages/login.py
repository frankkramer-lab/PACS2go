import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


dash.register_page(__name__)

# Login screen
layout = html.Form(
    [
        html.H2("Please log in to continue:", id="h1"),
        html.Div(children="", id="output-state", className="mb-3"), 
        dbc.Input(placeholder="Enter your username", type="text", id="uname-box", name='username', class_name="mb-3"),
        dbc.Input(placeholder="Enter your password", type="password", id="pwd-box", name='password', class_name="mb-3"),
        dbc.Button(children="Login", n_clicks=0, type="submit", id="login-button", color="success"),
    ], method='POST', className="w-50"
)
