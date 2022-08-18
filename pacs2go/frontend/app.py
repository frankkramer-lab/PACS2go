from dash import Dash, dcc, html, Input, Output, page_registry, page_container
import dash_bootstrap_components as dbc


app = Dash(name="xnat2go", pages_folder="/pacs2go/frontend/pages",use_pages=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP])

server = 'http://xnat-web:8080'

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
                dbc.NavLink("Home", href=page_registry['pacs2go.frontend.pages.home']['path']),
                dbc.NavLink(
                    "Projekte", href=page_registry['pacs2go.frontend.pages.projects']['path'], className="fw-lighter"),
                dbc.NavLink("Upload", href="", className="fw-lighter"),
            ],
            brand="PACS2go",
            color=colors['sage'],
            className="fw-bold mb-3",
            dark=True,
        ),
        html.Div([page_container], style={'padding': '1% 11%'})
    ]
)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, dev_tools_hot_reload=False)
