"""
Shared pytest fixtures for all tests.
"""
import os
import sys
import pytest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from flask import Flask, session
from werkzeug.security import generate_password_hash


# Patch auth globally before any module imports
@pytest.fixture(scope="session", autouse=True)
def patch_auth_globally():
    """Globally patch auth to avoid import-time decorator issues."""
    # This creates a mock auth that can be used throughout tests
    mock_auth = MagicMock()
    mock_auth.require_admin = lambda f: f
    mock_auth.require_login = lambda f: f
    mock_auth.require_role = lambda role: lambda f: f  # Mock decorator that just returns the function
    mock_auth.current_user = MagicMock(return_value='testadmin')
    mock_auth.get_user_role = MagicMock(return_value='administrator')
    
    # Patch before imports happen
    with patch.dict('sys.modules', {'lib.netdefense.auth.identitas_auth': mock_auth}):
        yield mock_auth


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def app(temp_dir):
    """Create a Flask app for testing with proper configuration."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.root_path = temp_dir
    
    # Create necessary directories
    os.makedirs(os.path.join(temp_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'static'), exist_ok=True)
    
    yield app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_mock():
    """Create a mock auth object."""
    auth = MagicMock()
    auth.require_admin = MagicMock(return_value=lambda f: f)
    auth.require_login = MagicMock(return_value=lambda f: f)
    auth.require_role = MagicMock(return_value=lambda f: f)
    auth.current_user = MagicMock(return_value='testuser')
    auth.get_user_role = MagicMock(return_value='administrator')
    return auth


def create_test_settings(temp_dir, settings=None):
    """Helper to create test settings file."""
    if settings is None:
        settings = {
            "site_title": "Test Site",
            "site_description": "Test Description",
            "posts_per_page": 10,
            "allow_registration": True,
            "require_comment_approval": False,
            "setup_completed": True
        }
    
    settings_file = os.path.join(temp_dir, "data", "settings.json")
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    with open(settings_file, 'w') as f:
        json.dump(settings, f)
    return settings_file


@pytest.fixture
def settings_file(temp_dir):
    """Create a test settings file."""
    return create_test_settings(temp_dir)
