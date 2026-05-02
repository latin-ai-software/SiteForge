import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock
from flask import Flask
import lib.newsletter as newsletter


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.root_path = tempfile.mkdtemp()
    yield app
    shutil.rmtree(app.root_path)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestNewsletter:
    def test_load_settings(self, app):
        """Test load_settings."""
        with app.app_context():
            # Create settings file
            settings_file = os.path.join(app.root_path, "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            test_settings = {"test": "value"}
            with open(settings_file, 'w') as f:
                json.dump(test_settings, f)

            settings = newsletter.load_settings()
            assert settings == test_settings

    def test_load_settings_no_file(self, app):
        """Test load_settings with no file."""
        with app.app_context():
            settings = newsletter.load_settings()
            assert settings == {}

    def test_get_newsletter_subscribers_path(self, app):
        """Test get_newsletter_subscribers_path."""
        with app.app_context():
            path = newsletter.get_newsletter_subscribers_path()
            expected = os.path.join(app.root_path, "data", "newsletter_subscribers.json")
            assert path == expected

    def test_load_newsletter_subscribers(self, app):
        """Test load_newsletter_subscribers."""
        with app.app_context():
            # Create subscribers file
            subscribers_file = newsletter.get_newsletter_subscribers_path()
            os.makedirs(os.path.dirname(subscribers_file), exist_ok=True)
            test_subscribers = ["test@example.com", "user@example.com"]
            with open(subscribers_file, 'w') as f:
                json.dump(test_subscribers, f)

            subscribers = newsletter.load_newsletter_subscribers()
            assert subscribers == test_subscribers

    def test_load_newsletter_subscribers_no_file(self, app):
        """Test load_newsletter_subscribers with no file."""
        with app.app_context():
            subscribers = newsletter.load_newsletter_subscribers()
            assert subscribers == []

    def test_save_newsletter_subscribers(self, app):
        """Test save_newsletter_subscribers."""
        with app.app_context():
            subscribers = ["test@example.com", "user@example.com"]
            result = newsletter.save_newsletter_subscribers(subscribers)
            assert result is True

            # Check file was created
            subscribers_file = newsletter.get_newsletter_subscribers_path()
            assert os.path.exists(subscribers_file)
            with open(subscribers_file, 'r') as f:
                data = json.load(f)
                assert set(data) == set(subscribers)

    def test_normalize_email(self):
        """Test normalize_email."""
        email = newsletter.normalize_email("  Test@Example.COM  ")
        assert email == "test@example.com"

    def test_is_valid_email(self):
        """Test is_valid_email."""
        assert newsletter.is_valid_email("test@example.com") is True
        assert newsletter.is_valid_email("invalid-email") is False
        assert newsletter.is_valid_email("") is False

    def test_subscribe_email(self, app):
        """Test subscribe_email."""
        with app.app_context():
            result = newsletter.subscribe_email("test@example.com")
            assert result[0] is True
            assert "Danke" in result[1]

            subscribers = newsletter.load_newsletter_subscribers()
            assert "test@example.com" in subscribers

    def test_subscribe_email_invalid(self, app):
        """Test subscribe_email with invalid email."""
        with app.app_context():
            result = newsletter.subscribe_email("invalid-email")
            assert result[0] is False
            assert "gültige" in result[1]

    def test_get_base_url(self, app):
        """Test get_base_url."""
        with app.app_context():
            with app.test_request_context('/'):
                base_url = newsletter.get_base_url()
                assert base_url == "http://localhost"

    @patch('smtplib.SMTP')
    def test_send_newsletter(self, mock_smtp, app):
        """Test send_newsletter."""
        with app.app_context():
            # Mock settings
            settings_file = os.path.join(app.root_path, "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump({
                    "ses_smtp_host": "smtp.example.com",
                    "ses_smtp_port": 587,
                    "ses_smtp_username": "user",
                    "ses_smtp_password": "pass",
                    "newsletter_sender_email": "sender@example.com",
                    "newsletter_enabled": True
                }, f)

            with app.test_request_context('/'):
                result = newsletter.send_newsletter(
                    "Subject",
                    "<p>Body</p>",
                    "Text body",
                    recipients=["recipient@example.com"]
                )
                assert result is True

    def test_get_newsletter_subscriber_count(self, app):
        """Test get_newsletter_subscriber_count."""
        with app.app_context():
            # Add some subscribers
            newsletter.subscribe_email("test1@example.com")
            newsletter.subscribe_email("test2@example.com")

            count = newsletter.get_newsletter_subscriber_count()
            assert count == 2