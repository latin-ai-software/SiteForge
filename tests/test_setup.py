import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from flask import Flask
from lib.routes.setup.index import (
    get_settings_file, get_data_dir, get_default_settings,
    load_settings, initialize_data_files, is_setup_completed,
    mark_setup_completed, setup_bp
)


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
    app.register_blueprint(setup_bp)
    yield app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestSetupFunctions:
    def test_get_settings_file(self, temp_dir):
        """Test get_settings_file."""
        path = get_settings_file(temp_dir)
        expected = os.path.join(temp_dir, 'data', 'settings.json')
        assert path == expected

    def test_get_data_dir(self, temp_dir):
        """Test get_data_dir."""
        path = get_data_dir(temp_dir)
        expected = os.path.join(temp_dir, 'data')
        assert path == expected

    def test_get_default_settings(self):
        """Test get_default_settings."""
        settings = get_default_settings()
        assert isinstance(settings, dict)
        assert 'site_title' in settings
        assert 'setup_completed' in settings
        assert settings['setup_completed'] is False

    def test_load_settings(self, temp_dir):
        """Test load_settings."""
        # Create settings file
        settings_file = get_settings_file(temp_dir)
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        test_settings = {"test": "value"}
        with open(settings_file, 'w') as f:
            json.dump(test_settings, f)

        settings = load_settings(temp_dir)
        assert settings["test"] == "value"
        assert "site_title" in settings  # Should have defaults merged

    def test_load_settings_no_file(self, temp_dir):
        """Test load_settings with no file."""
        settings = load_settings(temp_dir)
        assert "site_title" in settings  # Should have defaults
        assert settings["site_title"] == "My Awesome Site"

    def test_initialize_data_files(self, temp_dir):
        """Test initialize_data_files."""
        initialize_data_files(temp_dir)
        # Check if directories and files are created
        assert os.path.exists(os.path.join(temp_dir, 'data', 'posts'))
        assert os.path.exists(os.path.join(temp_dir, 'data', 'comments.json'))
        assert os.path.exists(os.path.join(temp_dir, 'data', 'posts_metadata.json'))

    def test_is_setup_completed(self, temp_dir):
        """Test is_setup_completed."""
        # Initially not completed
        assert is_setup_completed(temp_dir) is False

        # Create settings with setup_completed = True
        settings_file = get_settings_file(temp_dir)
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump({"setup_completed": True}, f)

        assert is_setup_completed(temp_dir) is True

    def test_mark_setup_completed(self, temp_dir):
        """Test mark_setup_completed."""
        # Create initial settings
        settings_file = get_settings_file(temp_dir)
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump({"test": "value"}, f)

        mark_setup_completed(temp_dir)

        with open(settings_file, 'r') as f:
            settings = json.load(f)
            assert settings["setup_completed"] is True
            assert settings["test"] == "value"


class TestSetupRoutes:
    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.redirect')
    @patch('lib.routes.setup.index.url_for')
    @patch('lib.routes.setup.index.render_template')
    def test_setup_page_not_completed(self, mock_render, mock_url_for, mock_redirect, mock_is_completed, app):
        """Test setup_page when setup not completed."""
        mock_is_completed.return_value = False

        with app.app_context():
            from lib.routes.setup.index import setup_page
            setup_page()
            mock_render.assert_called_once_with('setup/index.html')

    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.redirect')
    @patch('lib.routes.setup.index.url_for')
    def test_setup_page_completed(self, mock_url_for, mock_redirect, mock_is_completed, app):
        """Test setup_page when setup completed."""
        mock_is_completed.return_value = True
        mock_url_for.return_value = '/'

        with app.app_context():
            from lib.routes.setup.index import setup_page
            setup_page()
            mock_redirect.assert_called_once_with('/')

    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.IdentitasAuthManager')
    @patch('lib.routes.setup.index.initialize_data_files')
    @patch('lib.routes.setup.index.get_default_settings')
    @patch('lib.routes.setup.index.get_settings_file')
    @patch('lib.routes.setup.index.jsonify')
    def test_configure_success(self, mock_jsonify, mock_get_settings_file, mock_get_default, mock_init_data,
                              mock_auth_manager_class, mock_is_completed, app):
        """Test configure with valid data."""
        mock_is_completed.return_value = False
        mock_get_default.return_value = {"default": "settings"}
        mock_get_settings_file.return_value = "/tmp/settings.json"
        mock_auth = MagicMock()
        mock_auth.create_user.return_value = (True, "Success")
        mock_auth_manager_class.return_value = mock_auth
        mock_jsonify.return_value = {"success": True}

        with app.app_context():
            with patch('flask.request') as mock_request:
                mock_request.get_json.return_value = {
                    "site_title": "Test Site",
                    "admin_username": "admin",
                    "admin_password": "password123",
                    "admin_password_confirm": "password123"
                }

                from lib.routes.setup.index import configure
                result = configure()
                mock_jsonify.assert_called()

    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.jsonify')
    def test_configure_already_completed(self, mock_jsonify, mock_is_completed, app):
        """Test configure when setup already completed."""
        mock_is_completed.return_value = True
        mock_jsonify.return_value = {"success": False}

        with app.app_context():
            from lib.routes.setup.index import configure
            result = configure()
            mock_jsonify.assert_called_with({'success': False, 'message': 'Setup already completed'})

    @patch('lib.routes.setup.index.is_setup_completed')
    @patch('lib.routes.setup.index.jsonify')
    def test_configure_missing_fields(self, mock_jsonify, mock_is_completed, app):
        """Test configure with missing required fields."""
        mock_is_completed.return_value = False
        mock_jsonify.return_value = {"success": False}

        with app.app_context():
            with patch('flask.request') as mock_request:
                mock_request.get_json.return_value = {}

                from lib.routes.setup.index import configure
                result = configure()
                # Should call jsonify with error about site_title