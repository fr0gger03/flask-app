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
    postgres = PostgresContainer('postgres:16.4-alpine3.20')

    # Set up volume mapping for init scripts
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
# def client(db_session):
def client():
    """Flask test client to make HTTP requests."""

    app.testing = True
    with app.test_client() as client:
        yield client


def test_login_session(db_session, client):
    # """Fixture to log in a user and maintain session for testing purposes."""
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

    with client.application.test_request_context():
        response = client.get('/login')
        assert response.status_code == 200  # Adjust based on the app's response for successful login
        assert b'One of us' in response.data  # Adjust according to actual response content

        login_data = {'username': 'sally', 'password': 'sells seashells'}
        response = client.post('/login', data=login_data, follow_redirects=True)

        # assert response.status_code == 302
        # assert response.headers['Location'] == url_for('dashboard', _external=False)

        # Manually follow the redirection
        follow_response = client.get(response.headers['Location'], follow_redirects=True)

        # Assertions to check for successful login after following the redirect
        assert follow_response.status_code == 200
        assert b'Welcome' in follow_response.data  # Adjust according to the actual response content after login

# Test using Flask-SQLAlchemy
def test_docker_run_postgres_with_flask_sqlalchemy(db_session: scoped_session[Session]):
    # Ensure the app context is pushed for database operations
    with app.app_context():
        # Use the Flask-SQLAlchemy session (db.session) for executing raw SQL
        result = db.session.execute(text('SELECT version()'))
        row = result.fetchone()

        # Assertions to validate the PostgreSQL version
        assert row is not None
        assert row[0].lower().startswith("postgresql 16.4")


# Test the user creation via the SQLAlchemy model
def test_user_creation(db_session: scoped_session[Session]):
    # Create a test user
    hashed_password = bcrypt.generate_password_hash("sells seashells").decode('utf-8')
    user = User(username="sally", password=hashed_password)
    db_session.add(user)
    db_session.commit()
    # db.session.add(user)
    # db.session.commit()

    # Query the database for the user
    user_in_db = User.query.filter_by(username="sally").first()

    # Assertions to validate that the user exists and the password is hashed
    assert user_in_db is not None
    assert user_in_db.username == "sally"
    assert bcrypt.check_password_hash(user_in_db.password, "sells seashells")


def test_upload_get(client):
    response = client.get('/upload')
    assert response.status_code == 200
    assert b'Upload Excel File' in response.data  # Adjust according to your actual response content


def test_upload_post(login_session):
    """Test the file upload functionality."""
    # Specify the path to the file in your test directory
    file_path = os.path.join(os.path.dirname(__file__), 'test_files/', 'rvtools_file_sample.xlsx')
    
    # Open the file in binary mode for uploading
    with open(file_path, 'rb') as file:
        data = {
            'file': (file, 'rvtools_file_sample.xlsx')  # The filename can be the same or different
        }
        
        # Perform the file upload with the correct content type
        response = login_session.post('/upload', data=data, content_type='multipart/form-data')
    # Assert that the response status code is as expected
    assert response.status_code == 200 or response.status_code == 302  # Adjust based on app's behavior
    
    # Optionally, check if the response data contains success messages
    # Uncomment and adjust the line below if your app sends a success message in the response
    assert b'File uploaded successfully' in response.data  # Adjust according to actual response content
