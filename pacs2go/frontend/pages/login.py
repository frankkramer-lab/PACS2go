import dash
import dash_bootstrap_components as dbc
from dash import html


dash.register_page(__name__)

# Login screen
layout = dbc.Container(
    [
        html.H1("Welcome to PACS2go!", className="text-center mt-5"),
        html.Div(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Please log in to continue:", className="my-2")),
                        dbc.CardBody(
                            html.Form(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText(
                                            html.I(className="bi bi-person-fill"),
                                        ),
                                        dbc.Input(
                                            placeholder="Enter your username",
                                            type="text",
                                            id="uname-box",
                                            name='username',
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.InputGroup(
                                    [
                                        dbc.InputGroupText(
                                            html.I(className="bi bi-lock-fill"),
                                        ),
                                        dbc.Input(
                                            placeholder="Enter your password",
                                            type="password",
                                            id="pwd-box",
                                            name='password',
                                        ),
                                    ],
                                    className="mb-3",
                                ),
                                dbc.Button(
                                    "Login",
                                    n_clicks=0,
                                    type="submit",
                                    id="login-button",
                                    color="success",
                                    className="w-100",
                                ),
                                html.Div("", id="output-state", className="mt-3"),
                            ], method='POST'), style={'background-color': 'rgb(211, 228, 216)'}
                        ),
                    ],
                    className="mt-5"
                ),
            ),
    ],
    className="d-flex flex-column justify-content-center align-items-center vh-40"
)