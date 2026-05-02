import pytest
import json
import os
import tempfile
import shutil
from lib.data.comment_manager import CommentManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def comment_manager(temp_dir):
    """Create a CommentManager instance with a temporary directory."""
    return CommentManager(temp_dir)


class TestCommentManager:
    def test_init(self, temp_dir):
        """Test CommentManager initialization."""
        cm = CommentManager(temp_dir)
        assert cm.base_path == temp_dir
        assert cm.comments_file == os.path.join(temp_dir, "data", "comments.json")
        assert os.path.exists(cm.comments_file)

    def test_ensure_comments_file(self, temp_dir):
        """Test _ensure_comments_file creates the file if it doesn't exist."""
        cm = CommentManager(temp_dir)
        # File should already exist from init
        assert os.path.exists(cm.comments_file)
        # Remove it and test recreation
        os.remove(cm.comments_file)
        cm._ensure_comments_file()
        assert os.path.exists(cm.comments_file)
        with open(cm.comments_file, 'r') as f:
            data = json.load(f)
            assert data == {}

    def test_load_comments(self, comment_manager):
        """Test _load_comments."""
        # Add some test data
        test_data = {"test": "data"}
        with open(comment_manager.comments_file, 'w') as f:
            json.dump(test_data, f)
        data = comment_manager._load_comments()
        assert data == test_data

    def test_save_comments(self, comment_manager):
        """Test _save_comments."""
        test_data = {"test": "data"}
        comment_manager._save_comments(test_data)
        with open(comment_manager.comments_file, 'r') as f:
            data = json.load(f)
            assert data == test_data

    def test_add_comment(self, comment_manager):
        """Test add_comment."""
        comment_id = comment_manager.add_comment("post1", "author", "content")
        assert comment_id == "1"
        comments = comment_manager._load_comments()
        assert "post1" in comments
        assert len(comments["post1"]) == 1
        assert comments["post1"][0]["content"] == "content"

    def test_add_comment_with_parent(self, comment_manager):
        """Test add_comment with parent_id."""
        comment_manager.add_comment("post1", "author", "content")
        comment_id = comment_manager.add_comment("post1", "author2", "reply", parent_id="1")
        assert comment_id == "2"
        comments = comment_manager._load_comments()
        assert comments["post1"][1]["parent_id"] == "1"

    def test_get_comments(self, comment_manager):
        """Test get_comments."""
        comment_manager.add_comment("post1", "author", "content")
        comment_manager.add_comment("post1", "author2", "content2")
        comments = comment_manager.get_comments("post1")
        assert len(comments) == 2

    def test_get_comments_pending(self, comment_manager):
        """Test get_comments with pending status."""
        comment_manager.add_comment("post1", "author", "content")
        # Manually set status to pending
        comments = comment_manager._load_comments()
        comments["post1"][0]["status"] = "pending"
        comment_manager._save_comments(comments)
        pending_comments, stats = comment_manager.get_comments("post1", "pending")
        assert len(pending_comments) == 1

    def test_get_comments_nonexistent_post(self, comment_manager):
        """Test get_comments for non-existent post."""
        comments, stats = comment_manager.get_comments("nonexistent")
        assert comments == []

    def test_delete_comment(self, comment_manager):
        """Test delete_comment."""
        comment_id = comment_manager.add_comment("post1", "author", "content")
        success = comment_manager.delete_comment("post1", comment_id)
        assert success is True
        comments = comment_manager._load_comments()
        assert len(comments["post1"]) == 0

    def test_delete_comment_not_found(self, comment_manager):
        """Test delete_comment with non-existent comment."""
        success = comment_manager.delete_comment("post1", "999")
        assert success is False

    def test_clear_cache(self, comment_manager):
        """Test clear_cache."""
        # If cache is available, test clearing
        if comment_manager._comment_cache is not None:
            # Add something to cache if possible
            comment_manager.clear_cache()
            # Should not raise error
        else:
            comment_manager.clear_cache()
            # Should not raise error