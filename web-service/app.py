from this import d
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from tools.pseudonymize_dicom import pseudonymize
from tempfile import TemporaryDirectory
import os

app = Flask(__name__)
app.secret_key = 'random string'

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
    if request.method == 'POST':
        f = request.files['file']
        if f.filename.endswith(".dcm"):
            with TemporaryDirectory(dir="/") as tmpdirname:
                path = os.path.join(tmpdirname, f.filename)
                f.save(path)
                if 'p' in request.form:
                    # user gets zipped pseudonym and pseudonymized file
                    zip = pseudonymize(path,destination=tmpdirname)
                    return send_file(zip)
                if 'p-and-u' in request.form:
                    # user gets zipped pseudonym
                    zip = pseudonymize(path,destination=tmpdirname, upload=True)
                    flash('Upload was successful.')
                    return send_file(zip)
        else:
            flash('ERROR: File needs to be in DICOM format. If you want to pseudonymize this file use our DICOM converter.')
            return render_template('pseudonymizer.html', title="Pseudonymizer")

        


@app.route("/converter")
def converter():
    title = "DICOM converter"
    return render_template('dicom-converter.html', title=title)
