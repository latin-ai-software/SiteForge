"""Tests for admin settings routes."""
import pytest
import json
import os
from unittest.mock import patch, MagicMock, ANY
from flask import Flask
import lib.routes.admin.manage.settings.index as settings_module
from lib.routes.admin.manage.settings.index import admin_settings_bp


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    import tempfile
    import shutil
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def app(temp_dir):
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.root_path = temp_dir
    app.register_blueprint(admin_settings_bp)
    
    # Create necessary directories
    os.makedirs(os.path.join(temp_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, 'static'), exist_ok=True)
    
    yield app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


class TestAdminSettingsRoutes:
    """Test admin settings routes."""

    def test_admin_settings_index(self, client, temp_dir):
        """Test admin_settings_index route."""
        with patch('lib.routes.admin.manage.settings.index.render_template', return_value='rendered'):
            with client.session_transaction() as sess:
                sess['user'] = 'admin'
            with patch.object(settings_module.auth, 'get_user_role', return_value='administrator'):
                response = client.get('/admin/settings/')

        assert response.status_code == 200
        assert response.data == b'rendered'

    def test_save_settings_success(self, client, temp_dir):
        """Test save_settings with valid data."""
        with patch('lib.routes.admin.manage.settings.index.CSRFProtection.validate_token', return_value=True), patch('lib.routes.admin.manage.settings.index.rate_limiter.is_rate_limited', return_value=False):
            with client.session_transaction() as sess:
                sess['user'] = 'admin'
            with patch.object(settings_module.auth, 'get_user_role', return_value='administrator'):
                response = client.post('/admin/settings/', data={
                    '_csrf_token': 'token',
                    'site_title': 'Test Site',
                    'site_description': 'A test site',
                    'posts_per_page': '10',
                    'analytics_period_days': '30',
                    'ses_smtp_port': '587',
                    'newsletter_sender_email': 'test@example.com',
                    'analytics_tracking_id': 'G-TESTID',
                    'enable_analytics': 'on',
                    'allow_registration': 'on',
                    'require_comment_approval': 'on',
                    'allow_robot_indexing': 'on',
                    'robot_user_agents': 'Googlebot',
                    'cookie_consent_message': 'Hi',
                    'require_cookie_consent': 'on',
                    'embed_favicon_in_html': 'on',
                    'imprint_enabled': 'on',
                    'allow_password_change': 'on',
                    'header_background_enabled': 'on',
                    'show_social_links': 'on',
                    'twitter_handle': '@test',
                    'facebook_page': 'https://facebook.com/test',
                })

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'

        settings_file = os.path.join(temp_dir, 'data', 'settings.json')
        assert os.path.exists(settings_file)
        with open(settings_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data['site_title'] == 'Test Site'
        assert data['analytics_tracking_id'] == 'G-TESTID'

    def test_save_settings_missing_csrf(self, client):
        """Test save_settings rejects missing CSRF token."""
        with client.session_transaction() as sess:
            sess['user'] = 'admin'
        with patch.object(settings_module.auth, 'get_user_role', return_value='administrator'):
            response = client.post('/admin/settings/', data={})

        assert response.status_code == 403

    def test_cache_stats_route(self, client):
        """Test cache_stats route returns cache statistics."""
        with patch('lib.cache_utils.get_cache_stats', return_value={'hits': 1}):
            with client.session_transaction() as sess:
                sess['user'] = 'admin'
            with patch.object(settings_module.auth, 'get_user_role', return_value='administrator'):
                response = client.get('/admin/settings/cache/stats')

        assert response.status_code == 200
        assert response.get_json()['status'] == 'ok'
        assert response.get_json()['stats'] == {'hits': 1}

    def test_encryption_status_route(self, client):
        """Test encryption_status route returns config encryption status."""
        with patch('lib.security.ConfigEncryption') as mock_config_enc:
            mock_config_enc.return_value.get_status.return_value = {'encryption_enabled': False}
            with client.session_transaction() as sess:
                sess['user'] = 'admin'
            with patch.object(settings_module.auth, 'get_user_role', return_value='administrator'):
                response = client.get('/admin/settings/encryption/status')

        assert response.status_code == 200
        assert response.get_json() == {'encryption_enabled': False}
