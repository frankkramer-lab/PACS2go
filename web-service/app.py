from flask import Flask, render_template, request, redirect, send_file
from tools.pseudonymizer.pseudonymize_dicom import pseudonymize
from tempfile import TemporaryDirectory
import os

app = Flask(__name__)


@app.route("/")
def startpage():
    title = "PACS2go"
    return render_template('startpage.html', title=title)


@app.route("/pseudonymizer")
def pseudonymization():
    title = "Pseudonymizer"
    return render_template('pseudonymizer.html', title=title)


@app.route('/pseudonymize_file', methods=['POST','GET'])
def pseudonymize_file():
    print(request)
    if request.method == 'POST':
        f = request.files['file[]']
        with TemporaryDirectory(dir="/") as tmpdirname:
            path = os.path.join(tmpdirname, f.filename)
            f.save(path)
            # user gets zipped pseudonym and pseudonymized file 
            zip = pseudonymize(path)
            return send_file(zip)


@app.route("/converter")
def converter():
    title = "DICOM converter"
    return render_template('dicom-converter.html', title=title)
