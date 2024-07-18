import pytest
from src.app import app


@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'You shall not pass' in response.data  # Adjust according to your actual response content

def test_register(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b'You will be assimilated.' in response.data  # Adjust according to your actual response content

def test_login_get(client):
    response = client.get('/login')
    assert response.status_code == 200
    assert b'One of us, one of us...' in response.data  # Adjust according to your actual response content

def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 302  # Assuming logout redirects
    # Check if the response contains a redirect to the login page
    assert '/login' in response.headers['Location']
