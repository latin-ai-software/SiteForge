import pytest
import os
import json
from app import create_app
from config import TestingConfig

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_setup_completed():
    """Mock setup as completed for all tests."""
    import lib.routes.setup.index as setup_module
    original_is_setup_completed = setup_module.is_setup_completed

    def mock_is_setup_completed(base_path):
        return True

    setup_module.is_setup_completed = mock_is_setup_completed

    yield

    # Restore original function
    setup_module.is_setup_completed = original_is_setup_completed

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

def test_post_creation_requires_login(client):
    """Test that creating a post requires login."""
    response = client.post('/create/post', data={
        'title': 'Test Post',
        'content': 'Test content'
    })
    # Should redirect to login or return error
    assert response.status_code in [302, 403]