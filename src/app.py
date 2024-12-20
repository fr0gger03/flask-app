import os
import sys
import pandas as pd
from flask import Flask, flash, request, redirect, render_template, send_file, url_for
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

if 'pytest' in sys.modules:
    from src.data_validation import filetype_validation
    from src.transform_lova import lova_conversion
    from src.transform_rvtools import rvtools_conversion
else:
    from data_validation import filetype_validation
    from transform_lova import lova_conversion
    from transform_rvtools import rvtools_conversion

if 'pytest' in sys.modules:
    UPLOAD_FOLDER = './src/input/'
else:
    UPLOAD_FOLDER = 'input/'

ALLOWED_EXTENSIONS = {'xls','xlsx'}

def allowed_file(file_name):
    return '.' in file_name and \
           file_name.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'thisisasecretkey'

if 'pytest' in sys.modules:
    # Use the dynamic connection URL provided by the test container during tests
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_TEST_URI', 'postgresql://inventorydbuser:password@localhost:5432/inventorydb')
else:
    # Use the hostname "db" - defined in compose.yaml - as database hostname
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://inventorydbuser:password@db:5432/inventorydb'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(db.Model, UserMixin):
    __tablename__ = 'users_tb'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(180), nullable=False)


class Project(db.Model):
    __tablename__ = 'projects_tb'
    pid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('users_tb.id'))
    projectname = db.Column(db.String(20), nullable=False, unique=True)


class Workload(db.Model):
    __tablename__ = 'workloads_tb'
    vmid = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer, db.ForeignKey('projects_tb.pid'))
    mobid = db.Column(db.String(20))
    cluster = db.Column(db.String(40))
    virtualdatacenter = db.Column(db.String(40))
    os = db.Column(db.String(40))
    os_name = db.Column(db.String(40))
    vmstate = db.Column(db.String(20))
    vcpu = db.Column(db.Integer)
    vmname = db.Column(db.String(40))
    vram = db.Column(db.Integer)
    ip_addresses = db.Column(db.String(60))
    vinfo_provisioned = db.Column(db.Numeric(12,6))
    vinfo_used = db.Column(db.Numeric(12,6))
    vmdktotal = db.Column(db.Numeric(12,6))
    vmdkused = db.Column(db.Numeric(12,6))
    readiops = db.Column(db.Numeric(12,6))
    writeiops = db.Column(db.Numeric(12,6))
    peakreadiops = db.Column(db.Numeric(12,6))
    peakwriteiops = db.Column(db.Numeric(12,6))
    readthroughput = db.Column(db.Numeric(12,6))
    writethroughput = db.Column(db.Numeric(12,6))
    peakreadthroughput = db.Column(db.Numeric(12,6))
    peakwritethroughput = db.Column(db.Numeric(12,6))


class RegisterForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                if login_user(user):
                    return redirect(url_for('dashboard'))
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print(fieldName, err)
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
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
    return render_template('upload.html')


@app.route('/success/<input_path>/<file_type>/<file_name>')
@login_required
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
        vmdf_html = vm_data_df.to_html(classes=["table", "table-sm","table-striped", "text-center","table-responsive","table-hover", "table-dark"])
        return render_template('success.html', fn=file_name, ft=file_type, tables=[vmdf_html], titles=[''])
    else:
        print()
        print("Something went wrong.  Please check your syntax and try again.")


if __name__ == '__main__':
    app.run()
