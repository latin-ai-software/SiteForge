import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from lib.data.user_manager import UserManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def user_manager(temp_dir):
    """Create a UserManager instance with a temporary directory."""
    with patch('lib.data.user_manager.IdentitasAuthManager') as mock_auth_class:
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        yield UserManager(temp_dir)


class TestUserManager:
    def test_init(self, temp_dir):
        """Test UserManager initialization."""
        with patch('lib.data.user_manager.IdentitasAuthManager') as mock_auth:
            um = UserManager(temp_dir)
            assert um.base_path == temp_dir
            mock_auth.assert_called_once_with(temp_dir)

    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_get_all_users(self, mock_auth_class, temp_dir):
        """Test get_all_users."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.engine = MagicMock()
        mock_auth._get_user_role.return_value = "user"
        mock_auth.has_git_access.return_value = True

        # Mock SQLAlchemy session and User model
        mock_session = MagicMock()
        mock_session.__enter__.return_value = mock_session
        mock_user = MagicMock()
        mock_user.username = "testuser"
        mock_user.created_at = "2023-01-01"
        mock_session.query.return_value.all.return_value = [mock_user]

        from lib.data.user_manager import UserManager
        user_manager = UserManager(temp_dir)

        with patch('sqlalchemy.orm.Session', return_value=mock_session):
            users = user_manager.get_all_users()
            assert len(users) == 1
            assert users[0]["username"] == "testuser"

    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_role(self, mock_auth_class, temp_dir):
        """Test update_user_role."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_role.return_value = (True, "Success")

        from lib.data.user_manager import UserManager
        user_manager = UserManager(temp_dir)

        result = user_manager.update_user_role("testuser", "admin")
        assert result == (True, "Success")
        mock_auth.update_user_role.assert_called_once_with("testuser", "admin")

    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_update_user_git_access(self, mock_auth_class, temp_dir):
        """Test update_user_git_access."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.update_user_git_access.return_value = (True, "Success")

        from lib.data.user_manager import UserManager
        user_manager = UserManager(temp_dir)

        result = user_manager.update_user_git_access("testuser", True)
        assert result == (True, "Success")
        mock_auth.update_user_git_access.assert_called_once_with("testuser", True)

    @patch('lib.data.user_manager.IdentitasAuthManager')
    def test_delete_user(self, mock_auth_class, temp_dir):
        """Test delete_user."""
        mock_auth = MagicMock()
        mock_auth_class.return_value = mock_auth
        mock_auth.delete_user.return_value = True

        from lib.data.user_manager import UserManager
        user_manager = UserManager(temp_dir)

        result = user_manager.delete_user("testuser")
        assert result is True
        mock_auth.delete_user.assert_called_once_with("testuser")

    def test_clear_cache(self, user_manager):
        """Test clear_cache."""
        # If cache is available, test clearing
        if user_manager._user_cache is not None:
            user_manager.clear_cache()
            # Should not raise error
        else:
            user_manager.clear_cache()
            # Should not raise error