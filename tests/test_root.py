import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from flask import Flask
from lib.routes.root.index import (
    get_index_text, get_all_index_texts, root_bp
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
    app.register_blueprint(root_bp)
    yield app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestRootFunctions:
    def test_get_index_text(self, app):
        """Test get_index_text."""
        with app.app_context():
            # Create index texts file
            index_text_path = os.path.join(app.root_path, "data", "index_texts.json")
            os.makedirs(os.path.dirname(index_text_path), exist_ok=True)
            test_data = {
                "texts": [
                    {"id": "1", "content": "Test content", "active": True},
                    {"id": "2", "content": "Inactive content", "active": False}
                ]
            }
            with open(index_text_path, 'w') as f:
                json.dump(test_data, f)

            content = get_index_text()
            assert content == "Test content"

    def test_get_index_text_no_active(self, app):
        """Test get_index_text with no active text."""
        with app.app_context():
            index_text_path = os.path.join(app.root_path, "data", "index_texts.json")
            os.makedirs(os.path.dirname(index_text_path), exist_ok=True)
            test_data = {
                "texts": [
                    {"id": "1", "content": "Inactive content", "active": False}
                ]
            }
            with open(index_text_path, 'w') as f:
                json.dump(test_data, f)

            content = get_index_text()
            assert content == ""

    def test_get_index_text_no_file(self, app):
        """Test get_index_text with no file."""
        with app.app_context():
            content = get_index_text()
            assert content == ""

    def test_get_all_index_texts(self, app):
        """Test get_all_index_texts."""
        with app.app_context():
            index_text_path = os.path.join(app.root_path, "data", "index_texts.json")
            os.makedirs(os.path.dirname(index_text_path), exist_ok=True)
            test_data = {
                "texts": [
                    {"id": "1", "content": "Test content 1"},
                    {"id": "2", "content": "Test content 2"}
                ]
            }
            with open(index_text_path, 'w') as f:
                json.dump(test_data, f)

            texts = get_all_index_texts()
            assert len(texts) == 2
            assert texts[0]["content"] == "Test content 1"

    def test_get_all_index_texts_no_file(self, app):
        """Test get_all_index_texts with no file."""
        with app.app_context():
            texts = get_all_index_texts()
            assert texts == []


class TestRootRoutes:
    @patch('lib.routes.root.index.post_manager')
    @patch('lib.routes.root.index.post_manager.get_all_categories')
    @patch('lib.routes.root.index.render_template')
    def test_index(self, mock_render, mock_get_categories, mock_post_manager, app):
        """Test index route."""
        mock_post_manager.get_posts.return_value = []
        mock_get_categories.return_value = []

        with app.app_context():
            with patch('builtins.open', create=True) as mock_open:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                mock_file.read.return_value = '{"site_title": "Test"}'

                from lib.routes.root.index import index
                index()
                mock_render.assert_called()

    @patch('lib.routes.root.index.subscribe_email')
    @patch('lib.routes.root.index.render_template')
    def test_newsletter_get(self, mock_render, mock_subscribe, app, client):
        """Test newsletter GET route."""
        response = client.get('/newsletter')
        assert response.status_code == 200

    @patch('lib.routes.root.index.subscribe_email')
    @patch('lib.routes.root.index.render_template')
    def test_newsletter_post_success(self, mock_render, mock_subscribe, app, client):
        """Test newsletter POST route with success."""
        mock_subscribe.return_value = True

        response = client.post('/newsletter', data={'email': 'test@example.com'})
        assert response.status_code == 200

    @patch('lib.routes.root.index.subscribe_email')
    @patch('lib.routes.root.index.render_template')
    def test_newsletter_post_invalid_email(self, mock_render, mock_subscribe, app, client):
        """Test newsletter POST route with invalid email."""
        mock_subscribe.return_value = False

        response = client.post('/newsletter', data={'email': 'invalid-email'})
        assert response.status_code == 200

    @patch('lib.routes.root.index.get_all_index_texts')
    @patch('lib.routes.root.index.render_template')
    def test_index_text(self, mock_render, mock_get_texts, app, client):
        """Test index_text route."""
        mock_get_texts.return_value = [{"id": "1", "content": "Test"}]

        response = client.get('/index-text/1')
        assert response.status_code == 200

    @patch('lib.routes.root.index.comment_manager')
    @patch('lib.routes.root.index.render_template')
    def test_index_text_comment_post(self, mock_render, mock_comment_manager, app, client):
        """Test index_text comment POST route."""
        mock_comment_manager.add_comment.return_value = "1"

        response = client.post('/index-text/1/comment', data={
            'author': 'Test Author',
            'content': 'Test comment'
        })
        assert response.status_code == 302  # Redirect

    @patch('lib.routes.root.index.auth')
    @patch('lib.routes.root.index.render_template')
    def test_profile_me_get(self, mock_render, mock_auth, app, client):
        """Test profile GET route."""
        mock_auth.get_user.return_value = {"username": "test"}

        with patch('flask.session', {'user': 'test'}):
            response = client.get('/profile/me')
            assert response.status_code == 200

    @patch('lib.routes.root.index.post_manager')
    @patch('lib.routes.root.index.render_template')
    def test_search(self, mock_render, mock_post_manager, app, client):
        """Test search route."""
        mock_post_manager.search_posts.return_value = []

        response = client.get('/search?q=test')
        assert response.status_code == 200