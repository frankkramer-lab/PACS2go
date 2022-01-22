from flask import Flask, render_template, request, send_file, flash
from tools.pseudonymize_dicom import pseudonymize
from tempfile import TemporaryDirectory, tempdir
import os
import zipfile
import sys

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
        if f.filename.endswith(".dcm") or f.filename.endswith(".zip"):
            with TemporaryDirectory(dir="/") as tmpdirname:
                if f.filename.endswith(".dcm"):
                    path = os.path.join(tmpdirname, f.filename)
                    f.save(path)
                elif f.filename.endswith(".zip"):
                    try:
                        # extract zip file
                        with zipfile.ZipFile(f) as z:
                            z.extractall(tmpdirname)
                            print(os.listdir(tmpdirname)[0], flush=True)
                            # where to find the to-be-pseudonymized directory
                            path = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])
                    except:
                        flash('ERROR: invalid file')
                        return render_template('pseudonymizer.html', title="Pseudonymizer")
                # normal mode
                if 'p' in request.form:
                    # user gets zipped pseudonym and pseudonymized file
                    zip = pseudonymize(path,destination=tmpdirname)
                    return send_file(zip)
                # automized upload mode
                if 'p-and-u' in request.form:
                    # user gets zipped pseudonym
                    zip = pseudonymize(path,destination=tmpdirname, upload=True, from_web_request=True)
                    flash('Upload was successful.')
                    return send_file(zip)      
        else:
            # if no file or wrong format, re-render page and display message to user
            flash('ERROR: No file or wrong format. File needs to be in DICOM format. \n If you want to pseudonymize this file use our DICOM converter.')
            return render_template('pseudonymizer.html', title="Pseudonymizer")

        


@app.route("/converter")
def converter():
    title = "DICOM converter"
    return render_template('dicom-converter.html', title=title)
