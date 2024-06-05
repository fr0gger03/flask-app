
import os
from flask import Flask, flash, request, redirect, render_template, send_file, url_for
# from flask import Flask, request, , 
from werkzeug.utils import secure_filename
from transform import describe_import

app = Flask(__name__)

filename=''
total_vms=''
UPLOAD_FOLDER = 'input/'
ALLOWED_EXTENSIONS = {'xls','xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/success/<file_name>/<total_vms>')
def success(file_name, total_vms):
    # access the result in the tempalte, for example {{ vms }}
    return render_template('success.html', fn=file_name, vms=total_vms)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            file_type = request.form.get('file type')
            describe_params={"file_name":filename, "input_path":UPLOAD_FOLDER, "file_type":file_type}
            totalvms=describe_import(**describe_params)
            return redirect(url_for('success', file_name=filename, total_vms=totalvms))


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
