from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import pandas as pd

app = Dash(name="xnat2go", external_stylesheets=[dbc.themes.BOOTSTRAP])

colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}

app.layout = dbc.Container(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='PACS2go 2.0',
        style={
            'textAlign': 'left',
            'color': colors['text']
        }
    ),
    html.Div(children='Exchange medical files.', style={
        'textAlign': 'left',
        'color': colors['text']
    }),

])

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)