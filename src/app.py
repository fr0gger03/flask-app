
import os
from flask import Flask, flash, request, redirect, render_template, send_file, url_for
from werkzeug.utils import secure_filename
import pandas as pd
from data_validation import filetype_validation
from transform_lova import lova_conversion
from transform_rvtools import rvtools_conversion

app = Flask(__name__)

# filename=''
UPLOAD_FOLDER = 'input/'
ALLOWED_EXTENSIONS = {'xls','xlsx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            input_path=app.config['UPLOAD_FOLDER']
            filename = secure_filename(file.filename)
            file.save(os.path.join(input_path, filename))

            ft = filetype_validation(input_path, filename)
            return redirect(url_for('success', input_path=input_path, file_type=ft, file_name=filename))


@app.route('/success/<input_path>/<file_type>/<file_name>')
def success(input_path, file_type, file_name):
    describe_params={"file_name":file_name, "input_path":input_path}

    match file_type:
        case 'live-optics':
            vm_data_df = pd.DataFrame(lova_conversion(**describe_params))
        case 'rv-tools':
            vm_data_df = pd.DataFrame(rvtools_conversion(**describe_params))
        case 'invalid':
            return render_template('error.html', fn=file_name, ft=file_type)

    if vm_data_df is not None:
        # access the result in the tempalte, for example {{ vms }}
        vmdf_html = vm_data_df.to_html(classes=["table", "table-sm","table-striped", "text-center","table-responsive","table-hover"])
        return render_template('success.html', fn=file_name, ft=file_type, tables=[vmdf_html], titles=[''])
    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
