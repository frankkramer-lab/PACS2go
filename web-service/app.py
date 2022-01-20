from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def startpage():
    title = "PACS2go"
    return render_template('startpage.html', title=title)

@app.route("/pseudonymizer")
def pseudonymization():
    title = "Pseudonymizer"
    return render_template('pseudonymizer.html', title=title)

@app.route("/converter")
def converter():
    title = "DICOM converter"
    return render_template('pseudonymizer.html', title=title)
