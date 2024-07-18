import io
import pytest
from src.app import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client


def test_login_post(client):
    '''Testing login post - this will probably require Testcontainers with username and password in the database to test correctly...'''
    response = client.post('/login', data=dict(username='testuser', password='testpass'))
    assert b'Login successful' in response.data  # Adjust according to your actual response content


def test_upload_get(client):
    response = client.get('/upload')
    assert response.status_code == 302
    assert b'Upload Excel File' in response.data  # Adjust according to your actual response content


def test_upload_post(client):
    data = {
        'file': (io.BytesIO(b"some initial text data"), 'test.txt')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    assert b'File uploaded successfully' in response.data  # Adjust according to your actual response content
