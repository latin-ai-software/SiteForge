import pytest
import os
import json
import re
from flask import render_template
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


def test_admin_stylesheet_page_uses_shared_admin_layout(app):
    """Stylesheet management should render through the shared admin sidebar."""
    with app.test_request_context('/admin/manage/templates'):
        html = render_template('admin/manage/templates/index.html', stylesheets=[], active_theme=None)
        assert 'SiteForge Admin' in html
        assert 'Stylesheet Verwaltung' in html
        assert 'href="/admin/manage/templates"' in html


def test_admin_help_page_highlights_help_tab(app):
    """The help page should mark the help entry as active in the shared sidebar."""
    with app.test_request_context('/admin/help'):
        html = render_template('admin/help.html')
        assert re.search(r'<a href="/admin/help"[^>]*class="active"', html, re.S)


def test_admin_roles_page_highlights_roles_tab(app):
    """The roles page should activate the roles link instead of the users link."""
    with app.test_request_context('/admin/users/roles'):
        html = render_template('admin/base.html')
        assert re.search(r'<a href="/admin/users/roles"[^>]*class="active"', html, re.S)
        assert not re.search(r'<a href="/admin/users"[^>]*class="active"', html, re.S)


def test_license_validation_requires_runtime_fingerprint(tmp_path, monkeypatch):
    """License signatures must change when the runtime fingerprint changes."""
    import hashlib
    import hmac
    import _license_check

    secret = 'test-secret'
    monkeypatch.setenv('SITEFORGE_LICENSE_SECRET', secret)

    base_file = tmp_path / 'stub.txt'
    base_file.write_text('hello', encoding='utf-8')
    fingerprint = hashlib.sha256(str(base_file).encode('utf-8')).hexdigest()

    payload = f'license-key:{fingerprint}'.encode('utf-8')
    expected_sig = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()

    monkeypatch.setattr(_license_check, '_runtime_fingerprint', lambda base_dir: fingerprint)
    monkeypatch.setattr(_license_check, '_read_license_signature', lambda base_dir: expected_sig)

    assert _license_check._verify_local_signature(tmp_path, 'license-key') is True

    altered = tmp_path / 'altered.txt'
    altered.write_text('goodbye', encoding='utf-8')
    altered_fingerprint = hashlib.sha256(str(altered).encode('utf-8')).hexdigest()
    monkeypatch.setattr(_license_check, '_runtime_fingerprint', lambda base_dir: altered_fingerprint)

    assert _license_check._verify_local_signature(tmp_path, 'license-key') is False


def test_license_validation_skipped_in_ci():
    """Test that license validation is properly skipped in CI environments."""
    import os
    import sys
    from unittest.mock import patch, MagicMock
    
    # Mock the license check module to test the logic
    with patch('sys.modules', {'pytest': MagicMock()}):
        # Import should not fail when pytest is detected
        try:
            import _license_check
            # If we get here, the license check was skipped
            assert True
        except SystemExit:
            # If we get here, license validation ran and failed
            assert False, "License validation should be skipped in test environment"