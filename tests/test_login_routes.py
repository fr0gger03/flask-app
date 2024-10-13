import io
import os
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from sqlalchemy import text
import pytest
from sqlalchemy.orm.scoping import scoped_session
from src.app import app, bcrypt, db, User   
from testcontainers.postgres import PostgresContainer
from flask_bcrypt import Bcrypt
from flask import url_for

# Create a fixture for the Postgres container and initialize the schema
@pytest.fixture(scope='session', autouse=True)
def postgres_container():
    """Fixture to create the postgres container and generate the schema"""
    postgres = PostgresContainer('postgres:16.4-alpine3.20')
    script = Path(__file__).parent/ 'sql' / 'init-user-db.sh'
    postgres.with_volume_mapping(host=str(script), container=f"/docker-entrypoint-initdb.d/{script.name}")
    with postgres:
        yield postgres


@pytest.fixture(scope='function')
def db_session(postgres_container: PostgresContainer):
    """Fixture to handle database session and rollback after each test, without schema creation."""
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_container.get_connection_url()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        # Use Flask-SQLAlchemy's db.session instead of manually creating a scoped session
        session = db.session

        yield session  # Provide the session to the test

        # Rollback after test and cleanup
        trans.rollback()
        conn.close()
        db.session.remove()


# Create a fixture for the Flask test client
@pytest.fixture(scope="module")
def client():
    """Flask test client to make HTTP requests."""
    app.testing = True
    with app.test_client() as client:
        yield client


def test_login_session(db_session, client):
    # Create a test user
    hashed_password = bcrypt.generate_password_hash("sells seashells").decode('utf-8')
    user = User(username="sally", password=hashed_password)
    db_session.add(user)
    db_session.commit()

    # Query the database for the user
    user_in_db = User.query.filter_by(username="sally").first()

    # Assertions to validate that the user exists and the password is hashed
    assert user_in_db is not None
    assert user_in_db.username == "sally"
    assert bcrypt.check_password_hash(user_in_db.password, "sells seashells")

    # with client.application.test_request_context():
    response = client.get('/login')
    assert response.status_code == 200  # Adjust based on the app's response for successful login
    assert b'One of us' in response.data  # Adjust according to actual response content

    csrf_token = response.data.decode().split('name="csrf_token" type="hidden" value="')[1].split('"')[0]

    login_data = {'username': 'sally', 'password': 'sells seashells', "csrf_token": csrf_token}

    response = client.post('/login', data=login_data, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'] == url_for('dashboard', _external=False)

    response = client.get('/upload')
    assert response.status_code == 200
    assert b'Upload Excel File' in response.data  # Adjust according to your actual response content

    """Test the file upload functionality."""
    # Specify the path to the file in your test directory
    file_path = os.path.join(os.path.dirname(__file__), 'test_files/', 'rvtools_file_sample.xlsx')
    
    # Open the file in binary mode for uploading
    with open(file_path, 'rb') as file:
        file_name = "rvtools_file_sample.xlsx"
        data = {
            'file': (file, file_name)  # The filename can be the same or different
        }
        
        # Perform the file upload with the correct content type
        response = client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=False)
    # Assert that the response status code is as expected
    assert response.status_code == 302
    assert "success" in response.headers['Location']
    assert file_name in response.headers['Location']
