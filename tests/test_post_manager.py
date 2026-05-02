import pytest
import json
import os
import tempfile
import shutil
import subprocess
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from lib.data.post_manager import PostManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def post_manager(temp_dir):
    """Create a PostManager instance with a temporary directory."""
    return PostManager(temp_dir)


class TestPostManager:
    def test_init(self, temp_dir):
        """Test PostManager initialization."""
        pm = PostManager(temp_dir)
        assert pm.base_path == temp_dir
        assert pm.posts_dir == os.path.join(temp_dir, "data", "posts")
        assert pm.metadata_file == os.path.join(temp_dir, "data", "posts_metadata.json")
        assert os.path.exists(pm.metadata_file)

    def test_ensure_metadata_file(self, temp_dir):
        """Test _ensure_metadata_file creates the file if it doesn't exist."""
        pm = PostManager(temp_dir)
        # File should already exist from init
        assert os.path.exists(pm.metadata_file)
        # Remove it and test recreation
        os.remove(pm.metadata_file)
        pm._ensure_metadata_file()
        assert os.path.exists(pm.metadata_file)
        with open(pm.metadata_file, 'r') as f:
            data = json.load(f)
            assert data == {}

    @patch('subprocess.run')
    def test_run_git_command_success(self, mock_subprocess, post_manager):
        """Test _run_git_command with successful execution."""
        mock_subprocess.return_value.stdout = "success"
        success, result = post_manager._run_git_command("/tmp", ["status"])
        assert success is True
        assert result == "success"
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    def test_run_git_command_failure(self, mock_subprocess, post_manager):
        """Test _run_git_command with failure."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'git', stderr="error")
        success, result = post_manager._run_git_command("/tmp", ["status"])
        assert success is False
        assert result == "error"

    @patch('subprocess.run')
    def test_run_git_command_file_not_found(self, mock_subprocess, post_manager):
        """Test _run_git_command when git is not found."""
        mock_subprocess.side_effect = FileNotFoundError()
        success, result = post_manager._run_git_command("/tmp", ["status"])
        assert success is False
        assert result == "Git ist nicht installiert oder nicht im PATH verfügbar."

    def test_load_metadata(self, post_manager):
        """Test _load_metadata."""
        # Add some test data
        test_data = {"test": "data"}
        with open(post_manager.metadata_file, 'w') as f:
            json.dump(test_data, f)
        data = post_manager._load_metadata()
        assert data == test_data

    def test_save_metadata(self, post_manager):
        """Test _save_metadata."""
        test_data = {"test": "data"}
        post_manager._save_metadata(test_data)
        with open(post_manager.metadata_file, 'r') as f:
            data = json.load(f)
            assert data == test_data

    def test_build_survey(self, post_manager):
        """Test _build_survey."""
        survey = post_manager._build_survey("Question?", ["A", "B", "C"])
        assert survey is not None
        assert survey["question"] == "Question?"
        assert len(survey["options"]) == 3
        assert survey["options"][0]["text"] == "A"
        assert survey["options"][0]["id"] == "option-0"

    def test_build_survey_invalid(self, post_manager):
        """Test _build_survey with invalid input."""
        survey = post_manager._build_survey("", [])
        assert survey is None

    def test_generate_slug(self, post_manager):
        """Test _generate_slug."""
        slug = post_manager._generate_slug("Test Title!")
        assert slug == "test-title!"

    def test_create_post(self, post_manager):
        """Test create_post."""
        post_id = post_manager.create_post("Test Post", "Content", "author")
        assert post_id == "test-post"
        metadata = post_manager._load_metadata()
        assert post_id in metadata
        assert metadata[post_id]["title"] == "Test Post"

    def test_update_post(self, post_manager):
        """Test update_post."""
        post_id = post_manager.create_post("Test Post", "Content", "author")
        success = post_manager.update_post(post_id, title="Updated Title")
        assert success is True
        metadata = post_manager._load_metadata()
        assert metadata[post_id]["title"] == "Updated Title"

    def test_update_post_not_found(self, post_manager):
        """Test update_post with non-existent post."""
        success = post_manager.update_post("nonexistent", title="Title")
        assert success is False

    def test_vote_survey(self, post_manager):
        """Test vote_survey."""
        survey = post_manager._build_survey("Question?", ["A", "B"])
        post_id = post_manager.create_post("Test", "Content", "author", survey=survey)
        success, message = post_manager.vote_survey(post_id, "user1", "option-0")
        assert success is True

    def test_vote_survey_post_not_found(self, post_manager):
        """Test vote_survey with non-existent post."""
        success, message = post_manager.vote_survey("nonexistent", "user", "option-0")
        assert success is False
        assert message == "Post nicht gefunden"

    def test_get_post(self, post_manager):
        """Test get_post."""
        post_id = post_manager.create_post("Test", "Content", "author")
        post = post_manager.get_post(post_id)
        assert post is not None
        assert post["title"] == "Test"

    def test_get_post_not_found(self, post_manager):
        """Test get_post with non-existent post."""
        post = post_manager.get_post("nonexistent")
        assert post is None

    def test_get_posts(self, post_manager):
        """Test get_posts."""
        post_manager.create_post("Post 1", "Content 1", "author")
        post_manager.create_post("Post 2", "Content 2", "author")
        posts = post_manager.get_posts()
        assert len(posts) == 2

    def test_delete_post(self, post_manager):
        """Test delete_post."""
        post_id = post_manager.create_post("Test", "Content", "author")
        success = post_manager.delete_post(post_id)
        assert success is True
        metadata = post_manager._load_metadata()
        assert post_id not in metadata

    def test_delete_post_not_found(self, post_manager):
        """Test delete_post with non-existent post."""
        success = post_manager.delete_post("nonexistent")
        assert success is False

    def test_get_posts_by_category(self, post_manager):
        """Test get_posts_by_category."""
        post_manager.create_post("Post", "Content", "author", categories=["cat1"])
        posts = post_manager.get_posts_by_category("cat1")
        assert len(posts) == 1

    def test_get_posts_by_tag(self, post_manager):
        """Test get_posts_by_tag."""
        post_manager.create_post("Post", "Content", "author", tags=["tag1"])
        posts = post_manager.get_posts_by_tag("tag1")
        assert len(posts) == 1

    def test_get_all_categories(self, post_manager):
        """Test get_all_categories."""
        post_manager.create_post("Post", "Content", "author", categories=["cat1", "cat2"])
        categories = post_manager.get_all_categories()
        assert "cat1" in categories
        assert "cat2" in categories

    def test_get_all_tags(self, post_manager):
        """Test get_all_tags."""
        post_manager.create_post("Post", "Content", "author", tags=["tag1", "tag2"])
        tags = post_manager.get_all_tags()
        assert "tag1" in tags
        assert "tag2" in tags

    def test_search_posts(self, post_manager):
        """Test search_posts."""
        post_manager.create_post("Unique Title", "Content", "author")
        posts = post_manager.search_posts("Unique")
        assert len(posts) == 1

    def test_get_posts_by_author(self, post_manager):
        """Test get_posts_by_author."""
        post_manager.create_post("Post", "Content", "author1")
        post_manager.create_post("Post", "Content", "author2")
        posts = post_manager.get_posts_by_author("author1")
        assert len(posts) == 1