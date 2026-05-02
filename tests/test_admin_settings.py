import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from flask import Flask
from lib.routes.admin.manage.settings.index import admin_settings_bp


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def app(temp_dir):
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.root_path = temp_dir
    app.register_blueprint(admin_settings_bp)
    yield app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestAdminSettingsRoutes:
    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.render_template')
    def test_admin_settings_index(self, mock_render, mock_auth, app):
        """Test admin_settings_index."""
        mock_auth.require_admin = lambda: None  # Mock decorator

        with app.app_context():
            # Create settings file
            settings_file = os.path.join(app.root_path, "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump({"site_title": "Test"}, f)

            from lib.routes.admin.manage.settings.index import admin_settings_index
            admin_settings_index()
            mock_render.assert_called_with('admin/settings/index.html', settings={"site_title": "Test"}, available_plugins=set())

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.rate_limiter')
    @patch('lib.routes.admin.manage.settings.index.CSRFProtection')
    @patch('lib.routes.admin.manage.settings.index.validate_input')
    @patch('lib.routes.admin.manage.settings.index.InputValidator')
    @patch('lib.routes.admin.manage.settings.index.SecurityLogger')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    @patch('lib.routes.admin.manage.settings.index.schedule_restart')
    def test_save_settings_success(self, mock_schedule, mock_jsonify, mock_security_logger,
                                  mock_input_validator, mock_validate_input, mock_csrf,
                                  mock_rate_limiter, mock_auth, app):
        """Test save_settings with valid data."""
        mock_auth.require_admin = lambda: None
        mock_rate_limiter.is_rate_limited.return_value = False
        mock_csrf.validate_token.return_value = True
        mock_validate_input.return_value = "test"
        mock_input_validator.validate_email.return_value = True
        mock_jsonify.return_value = {"status": "success"}

        with app.app_context():
            with patch('flask.request') as mock_request:
                mock_request.form = {
                    "_csrf_token": "valid_token",
                    "site_title": "Test Site",
                    "site_description": "Description",
                    "posts_per_page": "10",
                    "allow_registration": "on",
                    "require_comment_approval": "on",
                    "allow_robot_indexing": "",
                    "robot_user_agents": "",
                    "require_cookie_consent": "on",
                    "enable_analytics": "",
                    "newsletter_sender_email": "test@example.com",
                    "domain": "http://localhost"
                }
                mock_request.remote_addr = "127.0.0.1"

                from lib.routes.admin.manage.settings.index import save_settings
                result = save_settings()
                mock_jsonify.assert_called()

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_encryption_status(self, mock_jsonify, mock_auth, app, client):
        """Test encryption_status route."""
        mock_auth.require_admin = lambda: None
        mock_jsonify.return_value = {"encryption_enabled": False}

        response = client.get('/admin/settings/encryption/status')
        assert response.status_code == 200

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.file_manager')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_cache_flush(self, mock_jsonify, mock_file_manager, mock_auth, app, client):
        """Test cache_flush route."""
        mock_auth.require_admin = lambda: None
        mock_file_manager.flush_cache.return_value = True
        mock_jsonify.return_value = {"status": "success"}

        response = client.post('/admin/settings/cache/flush')
        assert response.status_code == 200

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.current_app')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_cache_stats(self, mock_jsonify, mock_current_app, mock_auth, app, client):
        """Test cache_stats route."""
        mock_auth.require_admin = lambda: None
        mock_current_app.cache = MagicMock()
        mock_current_app.cache.get_stats.return_value = {"hits": 10, "misses": 5}
        mock_jsonify.return_value = {"stats": {"hits": 10, "misses": 5}}

        response = client.get('/admin/settings/cache/stats')
        assert response.status_code == 200

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.requests')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_update_check(self, mock_jsonify, mock_requests, mock_auth, app, client):
        """Test update_check route."""
        mock_auth.require_admin = lambda: None
        mock_response = MagicMock()
        mock_response.json.return_value = {"version": "1.0.0"}
        mock_requests.get.return_value = mock_response
        mock_jsonify.return_value = {"current_version": "0.1.0", "latest_version": "1.0.0"}

        response = client.get('/admin/settings/update/check')
        assert response.status_code == 200

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_update_status(self, mock_jsonify, mock_auth, app, client):
        """Test update_status route."""
        mock_auth.require_admin = lambda: None
        mock_jsonify.return_value = {"status": "idle"}

        response = client.get('/admin/settings/update/status')
        assert response.status_code == 200

    @patch('lib.routes.admin.manage.settings.index.auth')
    @patch('lib.routes.admin.manage.settings.index.updater')
    @patch('lib.routes.admin.manage.settings.index.jsonify')
    def test_update_install(self, mock_jsonify, mock_updater, mock_auth, app, client):
        """Test update_install route."""
        mock_auth.require_admin = lambda: None
        mock_updater.install_update.return_value = True
        mock_jsonify.return_value = {"status": "success"}

        response = client.post('/admin/settings/update/install', data={'version': '1.0.0', 'license_key': 'key'})
        assert response.status_code == 200