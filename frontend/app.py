from data_interface.xnat_pacs_data_interface import XNAT
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc


app = Dash(name="xnat2go", external_stylesheets=[dbc.themes.BOOTSTRAP])


colors = {
    'background': '#FFFFFF',
    'text': '#000000',
    'sage': '#8cb897'
}


app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dbc.NavbarSimple(
            children=[
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Projekte", href="/projects",
                            active="exact", className="fw-lighter"),
                dbc.NavLink("Upload", href="/page-2",
                            active="exact", className="fw-lighter"),
            ],
            brand="PACS2go",
            color=colors['sage'],
            className="fw-bold mb-3",
            dark=True,
        ),
        dbc.Container(id="page-content",
                      style={'backgroundColor': colors['background']})
    ]
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        content = [html.H1(
            children='PACS2go 2.0',
            style={
                'textAlign': 'left',
                'color': colors['text']
            }
        ),
            html.Div(children='Exchange medical files.', style={
                'textAlign': 'left',
                'color': colors['text']
            })]
        return content

    elif pathname == "/projects":
        table_header = [
            html.Thead(html.Tr([html.Th("Project Name"), html.Th("Number of Directories")]))
        ]

        with XNAT("admin", "admin") as connection:
            rows = []
            for p in connection.get_all_projects():
                rows.append(html.Tr([html.Td(p.name), html.Td(p.your_user_role)]))

        table_body = [html.Tbody(rows)]

        table = dbc.Table(table_header + table_body, bordered=True)

        content = [html.H1(
            children='Your Projects',
            style={
                'textAlign': 'left',
                'color': colors['text']
            }
        ),
            table
        ]
        return content

    elif pathname == "/page-2":
        return html.P("Oh cool, this is page 2!")
    # If the user tries to reach a different page, return a 404 message
    return html.Div(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ],
        className="p-3 bg-light rounded-3",
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
