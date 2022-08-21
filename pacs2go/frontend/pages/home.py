from dash import register_page, html

register_page(__name__, title='PACS2go 2.0', path='/')


def layout():
    return [html.H1(
        children='PACS2go 2.0',
        style={
            'textAlign': 'left',
        }),
        html.Div(children='Exchange medical files.', style={
            'textAlign': 'left',
        })
        # TODO: display cards with Projects, Upload links + maybe some stats about XNAT server (no. of files,..)
    ]
