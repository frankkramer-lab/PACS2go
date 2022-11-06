from dash import Dash, dcc, html, page_registry, page_container
import dash_bootstrap_components as dbc
from pacs2go.frontend.helpers import colors


app = Dash(name="xnat2go", pages_folder="/pacs2go/frontend/pages", use_pages=True,
           external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)

app.layout = html.Div(
    [
        # navigation bar on top
        dcc.Location(id="url"),
        dbc.NavbarSimple(
            children=[
                dbc.NavLink(
                    "Home", href=page_registry['pacs2go.frontend.pages.home']['path']),
                dbc.NavLink(
                    "Projects", href=page_registry['pacs2go.frontend.pages.project_list']['path'], className="fw-lighter"),
                dbc.NavLink(
                    "Upload", href=page_registry['pacs2go.frontend.pages.large_upload']['path'], className="fw-lighter"),
            ],
            brand="PACS2go",
            brand_href="/",
            color=colors['sage'],
            className="fw-bold mb-3",
            dark=True,
        ),
        # placeholder for each registered page (see pages folder)
        html.Div([page_container], style={'padding': '1% 11%'})
    ]
)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, dev_tools_hot_reload=False)
