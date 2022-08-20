from dash import register_page, html, dcc, callback, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc

register_page(__name__, title='PACS2go 2.0', path='/upload')


def uploader():
    # Upload drag and drop area
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
            # Don't allow multiple files to be uploaded
            multiple=False
        ),
        # placeholder for image preview / upload Button to appear
        html.Div(id='output-image-preview'),
    ])


def parse_contents(contents, filename):
    # display image preview and filename
    if filename.endswith('.jpg') or filename.endswith('.jpeg'):
        return dbc.Card(
            [
                dbc.CardBody(html.P(filename, className="card-text")),
                dbc.CardImg(src=contents, bottom=True)
            ])
    else:
        return html.H5(filename)



@callback(Output('output-image-preview', 'children'),
          Input('upload-image', 'contents'),
          State('upload-image', 'filename'))
def update_output(contents, filename):
    # get selected data (preview it) and display upload button
    if contents is not None:
        children = dbc.Row(
            [
                dbc.Col([parse_contents(contents, filename)]),
                dbc.Col([dbc.Button("Upload to XNAT", id="click-upload", size="lg", color="success", className="col-6 mx-auto mb-3"),
                        # placeholder for successful upload message
                        html.Div(id='output-upload')]),
            ], className="mt-3"
        ),
        return children


@callback(
    Output('output-upload', 'children'),
    Input('click-upload', 'n_clicks'),
    State('upload-image', 'contents')
)
def upload_to_xnat(contents, btn):
    # triggered by clicking on the upload button
    if "click-upload" == ctx.triggered_id:
        # TODO: implement xnat upload
        return html.Div("Upload successful")


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
