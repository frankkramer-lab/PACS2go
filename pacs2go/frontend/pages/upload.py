from dash import register_page, html, dcc, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

register_page(__name__, title='PACS2go 2.0', path='/upload')


def uploader():
    return html.Div([
        dcc.Upload(
            id='upload-image',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '2px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
            },
            # Allow multiple files to be uploaded
            multiple=False
        ),
        html.Div(id='output-image-upload'),
    ])


def parse_contents(contents, filename):
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        image = dbc.CardImg(src=contents, bottom=True)
    return dbc.Card(
    [
        dbc.CardBody(html.P(filename, className="card-text")),
        image
    ],
    style={"width": "100%"}
)


@callback(Output('output-image-upload', 'children'),
          Input('upload-image', 'contents'),
          State('upload-image', 'filename'))
def update_output(contents, filename):
    if contents is not None:
        children = dbc.Row(
            [
                dbc.Col([parse_contents(contents, filename)]),
                dbc.Col(dbc.Button("Upload to XNAT", size="lg", color="success", className="col-6 mx-auto")),
            ], className="mt-3"
        ),
        return children


def layout():
    return [html.H1(
        children='PACS2go 2.0 - Uploader',
        style={
            'textAlign': 'left',
        },
        className="mb-3"),
        dcc.Markdown(children='Please select a **zip** folder or a single file to upload. \n \n' +
                     'Accepted formats include **DICOM**, **NIFTI**, **JPEG** and **JSON**.'),
        uploader()
    ]
