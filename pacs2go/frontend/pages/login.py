import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__)

# Login screen
layout = dbc.Form(
    [
        html.H2("Please log in to continue:", className="mb-3"),
        dbc.Input(placeholder="Enter your username", type="text", id="uname-box", name='username', class_name="mb-3"),
        dbc.Input(placeholder="Enter your password", type="password", id="pwd-box", name='password', class_name="mb-3"),
        dbc.Button("Login", n_clicks=0, type="submit", id="login-button", color='success'),
        html.Div(id="output-state")
    ], method='POST', class_name="w-50"
)