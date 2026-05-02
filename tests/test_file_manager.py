import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from werkzeug.datastructures import FileStorage
from io import BytesIO
from lib.data.file_manager import FileManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_manager(temp_dir):
    """Create a FileManager instance with a temporary directory."""
    return FileManager(temp_dir)


class TestFileManager:
    def test_init(self, temp_dir):
        """Test FileManager initialization."""
        fm = FileManager(temp_dir)
        assert fm.base_path == temp_dir
        assert fm.uploads_dir == os.path.join(temp_dir, "data", "uploads")
        assert os.path.exists(fm.uploads_dir)

    def test_is_allowed_file(self, file_manager):
        """Test _is_allowed_file."""
        assert file_manager._is_allowed_file("test.txt") is True
        assert file_manager._is_allowed_file("test.exe") is False
        assert file_manager._is_allowed_file("test") is False  # No extension

    def test_is_allowed_file_custom_extensions(self, file_manager):
        """Test _is_allowed_file with custom extensions."""
        assert file_manager._is_allowed_file("test.custom", {"custom"}) is True
        assert file_manager._is_allowed_file("test.txt", {"custom"}) is False

    def test_generate_unique_filename(self, file_manager):
        """Test _generate_unique_filename."""
        filename = file_manager._generate_unique_filename("test.txt")
        assert filename.endswith(".txt")
        assert len(filename) > 4  # Should have UUID + extension

    def test_generate_unique_filename_no_extension(self, file_manager):
        """Test _generate_unique_filename with no extension."""
        filename = file_manager._generate_unique_filename("test")
        assert "." not in filename
        assert len(filename) > 0

    def test_is_binary_file(self, file_manager):
        """Test _is_binary_file."""
        assert file_manager._is_binary_file("test.mp3", b"content") is True
        assert file_manager._is_binary_file("test.txt", b"content") is False
        assert file_manager._is_binary_file("test.unknown", b"content") is False

    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_success(self, mock_malware_checker, file_manager):
        """Test save_file with successful upload."""
        mock_checker = MagicMock()
        mock_checker.scan_file.return_value = (True, "")
        mock_malware_checker.return_value = mock_checker

        # Create a mock file
        file_content = b"test file content"
        file = FileStorage(
            stream=BytesIO(file_content),
            filename="test.txt",
            content_type="text/plain"
        )

        result = file_manager.save_file(file)
        assert "success" in result
        assert "filename" in result

    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_too_large(self, mock_malware_checker, file_manager):
        """Test save_file with file too large."""
        mock_checker = MagicMock()
        mock_malware_checker.return_value = mock_checker

        # Create a large mock file
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        file = FileStorage(
            stream=BytesIO(large_content),
            filename="large.txt",
            content_type="text/plain"
        )

        result = file_manager.save_file(file, max_size_mb=10)
        assert "error" in result
        assert "too large" in result["error"].lower()

    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_malware_detected(self, mock_malware_checker, file_manager):
        """Test save_file with malware detected."""
        mock_checker = MagicMock()
        mock_checker.scan_file.return_value = (False, "Malware detected")
        mock_malware_checker.return_value = mock_checker

        file = FileStorage(
            stream=BytesIO(b"malware content"),
            filename="malware.txt",
            content_type="text/plain"
        )

        result = file_manager.save_file(file)
        assert "error" in result
        assert "malware" in result["error"].lower()

    @patch('lib.data.file_manager.MalwareChecker')
    def test_save_file_not_allowed(self, mock_malware_checker, file_manager):
        """Test save_file with not allowed file type."""
        mock_checker = MagicMock()
        mock_malware_checker.return_value = mock_checker

        file = FileStorage(
            stream=BytesIO(b"content"),
            filename="test.exe",
            content_type="application/x-msdownload"
        )

        result = file_manager.save_file(file)
        assert "error" in result
        assert "not allowed" in result["error"].lower()

    def test_delete_file(self, file_manager):
        """Test delete_file."""
        # Create a test file
        test_file = os.path.join(file_manager.uploads_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")

        result = file_manager.delete_file("test.txt")
        assert result is True
        assert not os.path.exists(test_file)

    def test_delete_file_not_found(self, file_manager):
        """Test delete_file with non-existent file."""
        result = file_manager.delete_file("nonexistent.txt")
        assert result is False

    def test_get_file_path(self, file_manager):
        """Test get_file_path."""
        path = file_manager.get_file_path("test.txt")
        expected = os.path.join(file_manager.uploads_dir, "test.txt")
        assert path == expected

    @patch('flask.current_app')
    def test_get_file_url(self, mock_current_app, file_manager):
        """Test get_file_url."""
        mock_app = MagicMock()
        mock_app.url_for.return_value = "/uploads/test.txt"
        mock_current_app.return_value = mock_app

        url = file_manager.get_file_url("test.txt")
        assert url == "/uploads/test.txt"

    def test_list_files(self, file_manager):
        """Test list_files."""
        # Create some test files
        test_files = ["test1.txt", "test2.jpg", "test3.pdf"]
        for filename in test_files:
            with open(os.path.join(file_manager.uploads_dir, filename), 'w') as f:
                f.write("test")

        files = file_manager.list_files()
        assert len(files) == 3
        assert all(f in files for f in test_files)