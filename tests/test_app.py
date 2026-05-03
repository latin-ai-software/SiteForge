import pytest
import os
import json
from app import create_app
from config import TestingConfig
from unittest.mock import patch

@pytest.fixture
def app():
    """Create and configure a test app instance."""
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_session(client):
    """A test client with authenticated session."""
    with client.session_transaction() as sess:
        sess['user'] = 'testadmin'
    return client


@pytest.fixture
def auth_patches():
    """Patches for auth methods."""
    with patch('lib.routes.admin.help.auth.current_user', return_value='testadmin'), \
         patch('lib.routes.admin.help.auth.get_user_role', return_value='administrator'):
        yield


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


def test_admin_help_route_renders(auth_session, auth_patches):
    """Test that the admin help page is available."""
    response = auth_session.get('/admin/help')
    assert response.status_code == 200
    assert b'Hilfe' in response.data or b'Help' in response.data


def test_admin_help_url_for_builds(app):
    """Test that the named admin_help endpoint can be built."""
    with app.test_request_context():
        assert app.url_for('admin_help') == '/admin/help'


def test_admin_templates_include_help_link():
    """Test that admin templates include a link to the help page."""
    admin_template_files = [
        'templates/admin/posts/index.html',
        'templates/admin/settings/index.html',
        'templates/admin/backup/index.html',
        'templates/admin/users/index.html',
        'templates/admin/theme_creator/new.html',
        'templates/admin/theme_creator/index.html',
        'templates/admin/theme_creator/edit.html',
        'templates/admin/backup/remote_settings.html',
        'templates/admin/manage/templates/index.html',
        'templates/admin/analytics/index.html',
        'templates/admin/media/index.html',
    ]
    project_root = os.path.dirname(os.path.dirname(__file__))
    for relative_path in admin_template_files:
        path = os.path.join(project_root, relative_path)
        assert os.path.exists(path), f"Missing template file: {relative_path}"
        content = open(path, encoding='utf-8').read()
        assert 'url_for(\'admin_help\')' in content or '/admin/help' in content, f"Help link missing in {relative_path}"


def test_admin_help_template_exists():
    """Test that the admin help template exists."""
    help_template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'admin', 'help.html')
    assert os.path.exists(help_template_path)
    content = open(help_template_path, encoding='utf-8').read()
    assert 'Hilfe' in content or 'Help' in content