import os
import json
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from lib.data.media_manager import MediaManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def media_manager(temp_dir):
    """Create a MediaManager instance with temp directory."""
    return MediaManager(temp_dir)


def test_init_creates_directories(media_manager, temp_dir):
    """Test that __init__ creates necessary directories."""
    assert os.path.exists(os.path.join(temp_dir, "data", "uploads"))
    assert os.path.exists(os.path.join(temp_dir, "data", "media_usage.json"))


def test_init_creates_usage_file(media_manager, temp_dir):
    """Test that __init__ creates media_usage.json if it doesn't exist."""
    usage_file = os.path.join(temp_dir, "data", "media_usage.json")
    assert os.path.exists(usage_file)
    with open(usage_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {}


def test_load_usage_success(media_manager, temp_dir):
    """Test _load_usage loads JSON successfully."""
    usage_file = os.path.join(temp_dir, "data", "media_usage.json")
    test_data = {"test.jpg": {"count": 5}}
    with open(usage_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f)
    
    result = media_manager._load_usage()
    assert result == test_data


def test_load_usage_file_not_exists(media_manager, temp_dir):
    """Test _load_usage returns empty dict if file doesn't exist."""
    usage_file = os.path.join(temp_dir, "data", "media_usage.json")
    os.remove(usage_file)
    
    result = media_manager._load_usage()
    assert result == {}


def test_load_usage_invalid_json(media_manager, temp_dir):
    """Test _load_usage handles invalid JSON."""
    usage_file = os.path.join(temp_dir, "data", "media_usage.json")
    with open(usage_file, "w", encoding="utf-8") as f:
        f.write("invalid json")
    
    result = media_manager._load_usage()
    assert result == {}


def test_save_usage(media_manager, temp_dir):
    """Test _save_usage saves data correctly."""
    test_data = {"test.jpg": {"count": 10}}
    media_manager._save_usage(test_data)
    
    usage_file = os.path.join(temp_dir, "data", "media_usage.json")
    with open(usage_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == test_data


def test_get_usage_summary_no_files(media_manager):
    """Test get_usage_summary with no files."""
    result = media_manager.get_usage_summary()
    assert result == []


def test_get_usage_summary_with_files(media_manager, temp_dir):
    """Test get_usage_summary with files."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    
    # Create test files
    test_files = [
        ("image.png", 1024),
        ("video.mp4", 2048),
        ("audio.mp3", 512),
        ("doc.pdf", 256),
        ("unknown.xyz", 128)
    ]
    
    for filename, size in test_files:
        path = os.path.join(upload_dir, filename)
        with open(path, "wb") as f:
            f.write(b"x" * size)
    
    # Set usage data
    usage_data = {"image.png": {"count": 5}, "video.mp4": {"count": 0}}
    media_manager._save_usage(usage_data)
    
    result = media_manager.get_usage_summary()
    
    assert len(result) == 5
    
    # Check image.png
    img = next(f for f in result if f["filename"] == "image.png")
    assert img["size"] == 1024
    assert img["usage_count"] == 5
    assert img["is_image"] is True
    assert img["is_video"] is False
    
    # Check video.mp4
    vid = next(f for f in result if f["filename"] == "video.mp4")
    assert vid["usage_count"] == 0
    assert vid["is_video"] is True
    
    # Check audio.mp3
    aud = next(f for f in result if f["filename"] == "audio.mp3")
    assert aud["is_audio"] is True
    
    # Check doc.pdf
    doc = next(f for f in result if f["filename"] == "doc.pdf")
    assert doc["is_document"] is True
    
    # Check unknown.xyz
    unk = next(f for f in result if f["filename"] == "unknown.xyz")
    assert unk["is_image"] is False
    assert unk["is_video"] is False
    assert unk["is_audio"] is False
    assert unk["is_document"] is False


def test_get_usage_summary_caches_result(media_manager, temp_dir):
    """Test that get_usage_summary caches results."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    path = os.path.join(upload_dir, "test.png")
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    # First call
    result1 = media_manager.get_usage_summary()
    assert len(result1) == 1
    
    # Modify file (should not affect cached result)
    os.remove(path)
    
    # Second call should return cached result
    result2 = media_manager.get_usage_summary()
    assert result2 == result1


def test_get_usage_summary_no_cache(monkeypatch, temp_dir):
    """Test get_usage_summary without cache."""
    monkeypatch.setattr('lib.data.media_manager._cache_available', False)
    from lib.data.media_manager import MediaManager
    media_manager = MediaManager(temp_dir)
    
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    path = os.path.join(upload_dir, "test.png")
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    result = media_manager.get_usage_summary()
    assert len(result) == 1
    assert media_manager._media_cache is None


def test_clear_cache(media_manager):
    """Test clear_cache method."""
    if media_manager._media_cache is not None:
        # Add something to cache
        media_manager._media_cache.set('test', 'value')
        assert media_manager._media_cache.get('test') == 'value'
        
        media_manager.clear_cache()
        assert media_manager._media_cache.get('test') is None


@patch('lib.data.media_manager._cache_available', False)
def test_clear_cache_no_cache(media_manager):
    """Test clear_cache when no cache is available."""
    media_manager.clear_cache()  # Should not raise error


def test_get_file_info_existing_file(media_manager, temp_dir):
    """Test get_file_info with existing file."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "test.png"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 1024)
    
    # Set usage data
    usage_data = {filename: {"count": 3, "items": ["post1", "post2"]}}
    media_manager._save_usage(usage_data)
    
    result = media_manager.get_file_info(filename)
    
    assert result is not None
    assert result["filename"] == filename
    assert result["path"] == path
    assert result["size"] == 1024
    assert result["usage_count"] == 3
    assert result["usage"] == ["post1", "post2"]
    assert result["is_image"] is True


def test_get_file_info_non_existing_file(media_manager):
    """Test get_file_info with non-existing file."""
    result = media_manager.get_file_info("nonexistent.png")
    assert result is None


def test_get_file_info_no_usage_data(media_manager, temp_dir):
    """Test get_file_info with no usage data."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "test.mp4"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 512)
    
    result = media_manager.get_file_info(filename)
    
    assert result is not None
    assert result["usage_count"] == 0
    assert result["usage"] == []
    assert result["is_video"] is True


def test_get_file_info_file_types(media_manager, temp_dir):
    """Test get_file_info file type detection."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    test_files = [
        ("image.jpg", "is_image"),
        ("video.mp4", "is_video"),
        ("audio.wav", "is_audio"),
        ("doc.pdf", "is_document"),
        ("unknown.xyz", None)
    ]
    
    for filename, expected_type in test_files:
        path = os.path.join(upload_dir, filename)
        with open(path, "wb") as f:
            f.write(b"x" * 100)
        
        result = media_manager.get_file_info(filename)
        assert result is not None
        
        if expected_type:
            assert result[expected_type] is True
        else:
            # For unknown, all should be False
            assert not result["is_image"]
            assert not result["is_video"]
            assert not result["is_audio"]
            assert not result["is_document"]


def test_get_file_info_no_extension(media_manager, temp_dir):
    """Test get_file_info with file without extension."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "noextension"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    result = media_manager.get_file_info(filename)
    
    assert result is not None
    assert result["is_image"] is False
    assert result["is_video"] is False
    assert result["is_audio"] is False
    assert result["is_document"] is False


def test_delete_file_existing(media_manager, temp_dir):
    """Test delete_file with existing file."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "test.png"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    # Set usage data
    usage_data = {filename: {"count": 2}}
    media_manager._save_usage(usage_data)
    
    success, message = media_manager.delete_file(filename)
    
    assert success is True
    assert message == "Datei gelöscht"
    assert not os.path.exists(path)
    
    # Check usage updated
    usage = media_manager._load_usage()
    assert filename not in usage


def test_delete_file_non_existing(media_manager):
    """Test delete_file with non-existing file."""
    success, message = media_manager.delete_file("nonexistent.png")
    
    assert success is False
    assert message == "Datei existiert nicht"


def test_delete_file_no_usage_data(media_manager, temp_dir):
    """Test delete_file when no usage data exists."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "test.png"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    success, message = media_manager.delete_file(filename)
    
    assert success is True
    assert message == "Datei gelöscht"
    assert not os.path.exists(path)


@patch('os.remove')
def test_delete_file_os_error(mock_remove, media_manager, temp_dir):
    """Test delete_file with OS error."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    filename = "test.png"
    path = os.path.join(upload_dir, filename)
    with open(path, "wb") as f:
        f.write(b"x" * 100)
    
    mock_remove.side_effect = OSError("Permission denied")
    
    success, message = media_manager.delete_file(filename)
    
    assert success is False
    assert "Fehler beim Löschen: Permission denied" in message
    # File should still exist
    assert os.path.exists(path)


def test_rename_file_success(media_manager, temp_dir):
    """Test rename_file successful rename."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "new.png"
    old_path = os.path.join(upload_dir, old_name)
    new_path = os.path.join(upload_dir, new_name)
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    # Set usage data
    usage_data = {old_name: {"count": 1}}
    media_manager._save_usage(usage_data)
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is True
    assert message == "Datei erfolgreich umbenannt"
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)
    
    # Check usage updated
    usage = media_manager._load_usage()
    assert old_name not in usage
    assert new_name in usage
    assert usage[new_name]["count"] == 1


def test_rename_file_add_extension(media_manager, temp_dir):
    """Test rename_file adds extension if missing."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "new"  # No extension
    old_path = os.path.join(upload_dir, old_name)
    new_path = os.path.join(upload_dir, "new.png")  # Should add .png
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is True
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)


def test_rename_file_different_extension(media_manager, temp_dir):
    """Test rename_file with different extension."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "new.jpg"  # Different extension
    old_path = os.path.join(upload_dir, old_name)
    new_path = os.path.join(upload_dir, "new.jpg.png")  # Should add .png
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is True
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)


def test_rename_file_non_existing(media_manager):
    """Test rename_file with non-existing file."""
    success, message = media_manager.rename_file("nonexistent.png", "new.png")
    
    assert success is False
    assert message == "Datei existiert nicht"


def test_rename_file_target_exists(media_manager, temp_dir):
    """Test rename_file when target already exists."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "existing.png"
    old_path = os.path.join(upload_dir, old_name)
    new_path = os.path.join(upload_dir, new_name)
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    with open(new_path, "wb") as f:
        f.write(b"y" * 100)
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is False
    assert message == "Eine Datei mit diesem Namen existiert bereits"
    assert os.path.exists(old_path)
    assert os.path.exists(new_path)


@patch('os.rename')
def test_rename_file_os_error(mock_rename, media_manager, temp_dir):
    """Test rename_file with OS error."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "new.png"
    old_path = os.path.join(upload_dir, old_name)
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    mock_rename.side_effect = OSError("Permission denied")
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is False
    assert "Fehler beim Umbenennen: Permission denied" in message
    assert os.path.exists(old_path)


def test_rename_file_no_usage_data(media_manager, temp_dir):
    """Test rename_file when no usage data exists."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    new_name = "new.png"
    old_path = os.path.join(upload_dir, old_name)
    new_path = os.path.join(upload_dir, new_name)
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    success, message = media_manager.rename_file(old_name, new_name)
    
    assert success is True
    assert not os.path.exists(old_path)
    assert os.path.exists(new_path)
    
    # Usage should remain empty
    usage = media_manager._load_usage()
    assert len(usage) == 0


def test_update_usage_after_rename_existing(media_manager):
    """Test _update_usage_after_rename with existing usage."""
    usage_data = {"old.png": {"count": 5}}
    media_manager._save_usage(usage_data)
    
    media_manager._update_usage_after_rename("old.png", "new.png")
    
    usage = media_manager._load_usage()
    assert "old.png" not in usage
    assert "new.png" in usage
    assert usage["new.png"]["count"] == 5


def test_update_usage_after_rename_non_existing(media_manager):
    """Test _update_usage_after_rename with non-existing old name."""
    usage_data = {"other.png": {"count": 1}}
    media_manager._save_usage(usage_data)
    
    media_manager._update_usage_after_rename("old.png", "new.png")
    
    usage = media_manager._load_usage()
    assert "old.png" not in usage
    assert "new.png" not in usage
    assert "other.png" in usage


def test_rename_file_empty_old_name(media_manager):
    """Test rename_file with empty old name."""
    success, message = media_manager.rename_file("", "new.png")
    
    assert success is False
    assert "Fehler beim Umbenennen" in message


def test_rename_file_empty_new_name(media_manager, temp_dir):
    """Test rename_file with empty new name."""
    upload_dir = os.path.join(temp_dir, "data", "uploads")
    old_name = "old.png"
    old_path = os.path.join(upload_dir, old_name)
    
    with open(old_path, "wb") as f:
        f.write(b"x" * 100)
    
    success, message = media_manager.rename_file(old_name, "")
    
    # Should rename to .png (empty name + extension)
    new_path = os.path.join(upload_dir, ".png")
    assert success is True
    assert os.path.exists(new_path)


def test_get_file_info_empty_filename(media_manager):
    """Test get_file_info with empty filename."""
    result = media_manager.get_file_info("")
    # Empty filename points to the upload directory, which exists
    assert result is not None
    assert result["filename"] == ""


def test_delete_file_empty_filename(media_manager):
    """Test delete_file with empty filename."""
    success, message = media_manager.delete_file("")
    
    assert success is False
    assert "Fehler beim Löschen" in message