from flask import Flask, render_template,request
app = Flask(__name__)


@app.route("/")
def startpage():
    title = "PACS2go"
    return render_template('startpage.html', title=title)

@app.route("/pseudonymizer")
def pseudonymization():
    title = "Pseudonymizer"
    return render_template('pseudonymizer.html', title=title)
    
@app.route('/pseudo_uploader', methods = ['POST'])
def pseudonymize_file():
   if request.method == 'POST':
      f = request.files['file']
      # f.save(f.filename)
      return 'file uploaded successfully'



@app.route("/converter")
def converter():
    title = "DICOM converter"
    return render_template('pseudonymizer.html', title=title)
