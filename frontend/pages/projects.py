import dash
from dash import html, dcc, callback, Input, Output

dash.register_page(__name__, title='Projects', path='/projects')

layout = html.Div(children=[
    html.H1(children='This is our Analytics page'),
	html.Div([
        "Select a city: ",
        dcc.RadioItems(['New York City', 'Montreal','San Francisco'],
        'Montreal',
        id='analytics-input')
    ]),
	html.Br(),
    html.Div(id='analytics-output'),
])


@callback(
    Output(component_id='analytics-output', component_property='children'),
    Input(component_id='analytics-input', component_property='value')
)
def update_city_selected(input_value):
    return f'You selected: {input_value}'







# rows = []
# with XNAT(server, "admin", "admin") as connection:
#     for p in connection.get_all_projects():
#         rows.append(html.Tr([html.Td(p.name), html.Td(p.your_user_role)]))
    
# @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
# def render_page_content(pathname):
#     if pathname == "/":
#         content = [html.H1(
#             children='PACS2go 2.0',
#             style={
#                 'textAlign': 'left',
#                 'color': colors['text']
#             }
#         ),
#             html.Div(children='Exchange medical files.', style={
#                 'textAlign': 'left',
#                 'color': colors['text']
#             })]
#         return content


#     elif pathname == "/projects":
#         table_header = [
#             html.Thead(html.Tr([html.Th("Project Name"), html.Th("Column 2")]))
#         ]

#         # rows = html.Tr([html.Td("hi"), html.Td("hey")])
#         # try:
#         #     with XNAT(server,"admin", "admin") as connection:
#         #         for p in connection.get_all_projects():
#         #             rows.append(html.Tr([html.Td(p.name), html.Td(p.your_user_role)]))
#         # except:
#         #     return html.H1("404: Not found", className="text-danger"),

#         table_body = [html.Tbody(rows)]

#         table = dbc.Table(table_header + table_body, bordered=True)

#         content = [html.H1(
#             children='Your Projects',
#             style={
#                 'textAlign': 'left',
#                 'color': colors['text']
#             }
#         ),
#             table
#         ]
#         return content

#     elif pathname == "/page-2":
#         return html.P("Oh cool, this is page 2!")
#     # If the user tries to reach a different page, return a 404 message
#     return html.Div(
#         [
#             html.H1("404: Not found", className="text-danger"),
#             html.Hr(),
#             html.P(f"The pathname {pathname} was not recognised..."),
#         ],
#         className="p-3 bg-light rounded-3",
#     )