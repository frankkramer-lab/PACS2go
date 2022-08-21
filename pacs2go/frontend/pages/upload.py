import base64
import tempfile
from dash import register_page, html, dcc, callback, ctx
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from pacs2go.data_interface.xnat_pacs_data_interface import XNAT, XNATProject

register_page(__name__, title='PACS2go 2.0', path='/upload')

server = 'http://xnat-web:8080'

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
    State('upload-image', 'contents'),
    State('upload-image', 'filename')
)
def upload_to_xnat(btn, contents, filename):
    # triggered by clicking on the upload button
    if "click-upload" == ctx.triggered_id:
        # TODO: implement xnat upload
        with tempfile.NamedTemporaryFile(suffix=filename) as tf:
            try:
                # https://docs.faculty.ai/user-guide/apps/examples/dash_file_upload_download.html
                data = contents.encode("utf8").split(b";base64,")[1]
                tf.write(base64.b64decode(data))
                print(tf.name)
                with XNAT(server,'admin','admin') as connection:
                    # upload to XNAT server
                    XNATProject(connection,'test6').insert_file_into_project(tf.name)
                return html.Div("Upload successful")
            except Exception as err:
                print(err.with_traceback())
                return html.Div("Upload unsuccessful: " + str(err))
    return html.Div("")


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
