import dash
from dash import html
#from app import colors

dash.register_page(__name__, title='PACS2go 2.0', path='/')

layout = [html.H1(
    children='PACS2go 2.0',
    style={
        'textAlign': 'left',
    }
),
    html.Div(children='Exchange medical files.', style={
        'textAlign': 'left',
    })]
