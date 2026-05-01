import pytest
from app import app as flask_app
from config import TestingConfig

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    flask_app.config.from_object(TestingConfig)
    return flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_home_page(client):
    """Test that home page loads."""
    response = client.get('/')
    assert response.status_code == 200

def test_post_creation_requires_login(client):
    """Test that creating a post requires login."""
    response = client.post('/create/post', data={
        'title': 'Test Post',
        'content': 'Test content'
    })
    # Should redirect to login or return error
    assert response.status_code in [302, 403]