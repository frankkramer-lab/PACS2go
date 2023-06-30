import dash
import dash_bootstrap_components as dbc
from dash import callback
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from pacs2go.frontend.helpers import colors


dash.register_page(__name__)


@callback(Output("card-content", "children"), [Input("card-tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-1":
        # German
        return dcc.Markdown('''
            ## Bedienungsanleitung PACS2go

            Herzlich willkommen bei PACS2go! Dieser Leitfaden soll Ihnen helfen, das System optimal zu nutzen und Ihre Bildverwaltung effizienter zu gestalten.

            ### Projekte

            Alle Projekte finden sie unter dem 'Projekte' Navigationslink, der oben angeheftet ist. **Projekte** bilden die größte Einheit in diesem System und können mehrere Unterordner bzw. **Directories** enthalten, welche widerrum schließlich die Dateien bzw. **Files**, welche ausgetauscht werden sollen, enthalten. 

            Wenn Sie ein neues Projekt erstellen möchten, klicken Sie auf 'Projekte' und dann auf 'Create new project'. Geben Sie einen eindeutigen Namen für das Projekt an und fügen Sie optional eine Beschreibung und Schlagwörter hinzu, um es leichter wiederzufinden.

            ### Nutzerrollen
            Ihre Rechte innerhalb eines Projekts hängen von ihrer Nutzerrolle ab, die sich von Projekt zu Projekt unterscheiden kann. 
            Es gibt 3 Rollen: 
            - **Owner**: Vollzugriff auf das Projekt
            - **Member**: Hochladen von Dateien, jedoch keine Löschrechte
            - **Collaborator**: Leserechte und Downloadmöglichkeit
            - außerdem: keine Rechte -> Projekt erscheint nicht in der Liste

            ### Hochladen von Dateien

            Um Dateien hochzuladen, nutzen Sie den Navigationslink "Upload" oder klicken Sie direkt in einem Projekt auf "Insert". Beim Hochladen können Sie folgende Parameter angeben:
            - Projekt-Name: Auswahl aus vorhandenen Projekten. Dies ist ein Pflichtfeld.
            - Directory-Name: Auswahl aus vorhandenen Directories oder Angabe eines neuen Names, wodurch ein neues Directory erstellt wird
            - File Tags: Verwenden Sie Schlagwörter, um Ihre hochgeladenen Dateien leichter zu finden. Geben Sie die Schlagwörter durch Kommas getrennt ein (z.B. "Melanom, ID47x83, Dermatologie").

            Sie können einzelne Dateien oder komprimierte Ordner im ZIP-Format hochladen. ZIP-Dateien werden automatisch entpackt. Nach dem erfolgreichen Upload erscheint der Button "Upload to XNAT". Erst wenn Sie diesen Button betätigen, werden die Dateien auf dem XNAT-Server abgelegt und sind für Sie zugänglich.

            ### Dateien einsehen

            Die Ansicht "Viewer" ermöglicht es Ihnen, verschiedene Bildformate sowie CSV- und JSON-Dateien anzusehen. Gehen Sie dazu in ein Projekt und navigieren Sie zu einem Verzeichnis. Hier können Sie entweder den 'Viewer' Button betätigen oder eine einzelne Datei aus der Liste anklicken. In der Viewer-Ansicht können Sie aus einem Dropdown jede Datei des Directory auswählen und betrachten, insofern das Format dies erlaubt. DICOM Dateien stellen zusätzlich eine festem Auswahl ihrer Metadaten dar. 


            ### Troubleshooting & Kontakt

            Sollte anstelle der Projekte eine rote Box angezeigt werden, melden Sie sich bitte ab und wieder an, um Ihre Sitzung zu aktualisieren. Bei weiteren Fragen, Anregungen oder Schwierigkeiten wenden Sie sich gerne an uns unter [tamara.krafft@uni-a.de](mailto:tamara.krafft@uni-a.de) oder [dennis.hartmann@uni-a.de](mailto:dennis.hartmann@uni-a.de).
            '''),
    elif at == "tab-2":
        # English
        return dcc.Markdown('''
            ## How to use PACS2go

            Welcome to PACS2go! This guide is designed to help you make the most of the system and streamline your data management.

            ### Projects and User Roles

            All projects can be found under the "Projects" navigation link, located at the top. **Projects** are the main units in this system and can contain multiple **directories**, which in turn house the **files** to be exchanged.

            To create a new project, click on "Projects" and then select "Create new project". Provide a unique name for the project and optionally add a description and keywords to make it easier to find.

            ### User rights
            Your permissions within a project depend on your user role, which may vary from project to project. There are 3 roles:
            - **Owner**: Full access to the project
            - **Member**: Can upload files but cannot delete them
            - **Collaborator**: Read-only access with the ability to download files
            - Additionally: No access rights -> project does not appear in the list


            ### Uploading Files

            To upload files, use the "Upload" navigation link or click on "Insert" directly within a project. When uploading, you can specify the following parameters:
            - Project Name: Choose from existing projects. This field is required.
            - Directory Name: Choose from existing directories or enter a new name to create a new directory.
            - File Tags: Use keywords to make it easier to find your uploaded files. Separate the tags with commas (e.g., "Melanoma, ID47x83, Dermatology").

            You can upload individual files or compressed folders in ZIP format. ZIP files will be automatically extracted. After a successful upload, the "Upload to XNAT" button will appear. Only when you click this button will the files be stored on the XNAT server and become accessible to you.

            ### Viewing Files

            The "Viewer" allows you to view various image formats, as well as CSV and JSON files. To access it, navigate to a project and go to a directory. From there, you can either click on the "Viewer" button or select an individual file from the list. In the Viewer, you can choose any file from the directory using a dropdown menu. DICOM files also offer a selection of their metadata.

            ### Troubleshooting & Contact

            If a red box appears instead of projects, please log out and log back in to refresh your session. For further questions, suggestions, or difficulties, feel free to contact us at [tamara.krafft@uni-a.de](mailto:tamara.krafft@uni-a.de) or [dennis.hartmann@uni-a.de](mailto:dennis.hartmann@uni-a.de).'''),
    return html.P("This should never be displayed...")


#################
#  Page Layout  #
#################

def layout():
    return html.Div(
        [
            # Breadcrumb
            html.Div(
                [
                    dcc.Link("Home", href="/",
                             style={"color": colors['sage'], "marginRight": "1%"}),
                    html.Span(" > ", style={"marginRight": "1%"}),
                    html.Span("Help", className='active fw-bold', style={"color": "#707070"})],
                className='breadcrumb'),

            # Page title
            html.H1(f"Help", style={
                'textAlign': 'left'}, className="mb-3"),
            
            # Bilingual Instructions
            dbc.Card([
                dbc.CardHeader(
                    dbc.Tabs(
                        [
                            dbc.Tab(label="Deutsch", tab_id="tab-1"),
                            dbc.Tab(label="English", tab_id="tab-2"),
                        ],
                        id="card-tabs",
                        active_tab="tab-1",
                    )
                ),
                dbc.CardBody(html.Div(id="card-content",
                                      className="card-text m-3")),
            ]
            )
        ]
    )
