from flask import Flask, render_template, request, send_file, flash
from tools.pseudonymize_dicom import pseudonymize
from tools.convert2dicom import convert
from tempfile import TemporaryDirectory
import os
import zipfile


app = Flask(__name__)
app.secret_key = 'V$($ZTT9' # necessary for flash(), otherwise RunTimeError

@app.route("/")
def startpage():
    # render start/home page
    title = "PACS2go"
    return render_template('startpage.html', title=title)


@app.route("/pseudonymizer")
def pseudonymization():
    # render pseudonymizer template
    title = "Pseudonymizer"
    return render_template('pseudonymizer.html', title=title)


@app.route('/pseudonymize_file', methods=['POST','GET'])
def pseudonymize_file():
    if request.method == 'POST':
        f = request.files['file']
        if f.filename.endswith(".dcm") or f.filename.endswith(".zip"):
            with TemporaryDirectory(dir="/") as tmpdirname:
                if f.filename.endswith(".dcm"):
                    # handeling a single file
                    path = os.path.join(tmpdirname, f.filename)
                    f.save(path)
                elif f.filename.endswith(".zip"):
                    # handeling a zipped directory of DICOM files
                    try:
                        # extract zip file
                        with zipfile.ZipFile(f) as z:
                            z.extractall(tmpdirname)
                            # where to find the to-be-pseudonymized directory
                            path = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])
                    except:
                        flash('ERROR: invalid file')
                        return render_template('pseudonymizer.html', title="Pseudonymizer")
                # actual pseudonymization in two possible modes
                # normal mode
                if 'p' in request.form:
                    try:
                        # user gets zipped pseudonym and pseudonymized file
                        zip = pseudonymize(path,destination=tmpdirname)
                        return send_file(zip)
                    except:
                        flash('Something went wrong. File could not be pseudonymized.')
                        return render_template('pseudonymizer.html', title="Pseudonymizer")
                # automized upload mode
                if 'p-and-u' in request.form:
                    try:
                    # user gets zipped pseudonym
                        zip = pseudonymize(path,destination=tmpdirname, upload=True, from_web_request=True)
                        flash('Upload was successful.')
                        return send_file(zip) 
                    except:
                        flash('Something went wrong. File could not be pseudonymized.')
                        return render_template('pseudonymizer.html', title="Pseudonymizer")     
        else:
            # if no file or wrong format, re-render page and display message to user
            flash('ERROR: No file or wrong format. File needs to be in DICOM format. If you want to pseudonymize this file use our DICOM converter.')
            return render_template('pseudonymizer.html', title="Pseudonymizer")

        


@app.route("/converter")
def converter():
    # render converter template
    title = "DICOM converter"
    return render_template('dicom-converter.html', title=title)


@app.route('/convert_file', methods=['POST','GET'])
def convert_file():
    if request.method == 'POST':
        f = request.files['file']
        if f.filename != '':
            if not f.filename.endswith(".dcm"):
                # use temp directory to open zip file
                with TemporaryDirectory(dir="/") as tmpdirname:
                    if f.filename.endswith(".zip"):
                        # for converting a whole (zipped) directory
                        try:
                            # extract zip file to temporary directory
                            with zipfile.ZipFile(f) as z:
                                z.extractall(tmpdirname)
                                # where to find the to-be-pseudonymized directory
                            path = os.path.join(tmpdirname, os.listdir(tmpdirname)[0])
                        except:
                            flash('ERROR: invalid file')
                            return render_template('dicom-converter.html', title="DICOM converter")
                    else:
                        # for converting a single file
                        path = os.path.join(tmpdirname, f.filename)
                        f.save(path)
                    # actual file conversion in two possible modes
                    # normal mode
                    if 'c' in request.form:
                        try:
                        # user gets zipped converted file
                            zip = convert(path,destination=tmpdirname)
                            return send_file(zip)
                        except:
                            flash('Something went wrong. File could not be converted.')
                            return render_template('dicom-converter.html', title="DICOM converter")
                    # automized upload mode
                    if 'c-and-u' in request.form:
                        try:
                            # return value is not used, since nothing was saved -> direct upload
                            convert(path,destination=tmpdirname, upload=True, from_web_request=True)
                            flash('Upload was successful.')
                        except:
                            flash('Something went wrong. File could not be converted.')
                        return render_template('dicom-converter.html', title="DICOM converter")
            else:
                # if wrong format, re-render page and display message to user
                flash('ERROR: File is already DICOM format.')
                return render_template('dicom-converter.html', title="DICOM converter")
        else:
             # if no file was chosen, re-render page and display message to user
            flash('ERROR: No file was chosen')
            return render_template('dicom-converter.html', title="DICOM converter")

