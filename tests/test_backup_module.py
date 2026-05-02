import os
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from lib.routes.admin.manage import backup as backup_module


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.secret_key = "testsecret"
    return app


@pytest.fixture
def backup_env(tmp_path, monkeypatch):
    backup_dir = tmp_path / "backups"
    source_dir = tmp_path / "data" / "posts"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "post.md").write_text("hello")

    monkeypatch.setattr(backup_module, "BACKUP_DIR", str(backup_dir))
    monkeypatch.setattr(backup_module, "BACKUP_TARGETS", [str(source_dir)])

    return backup_dir


def test_create_backup_file_creates_zip(backup_env):
    filename, filepath = backup_module.create_backup_file()

    assert filename.endswith(".zip")
    assert os.path.exists(filepath)
    assert zipfile.is_zipfile(filepath)


def test_list_backups_returns_existing_zips(backup_env):
    filename, _ = backup_module.create_backup_file()
    backups = backup_module.list_backups()

    assert backups
    assert backups[0]["name"] == filename


def test_cleanup_old_backups_removes_excess_files(backup_env):
    backup_module.ensure_backup_dir()
    for index in range(12):
        path = backup_env / f"backup_extra_{index}.zip"
        path.write_text("x")

    backup_module.cleanup_old_backups(limit=10)

    zips = [name for name in os.listdir(backup_env) if name.endswith(".zip")]
    assert len(zips) == 10


def test_backup_index_route_uses_render_template(app):
    with patch.object(backup_module, "list_backups", return_value=[]), patch.object(backup_module, "render_template", return_value="rendered") as mock_render:
        result = backup_module.backup_index()

        assert result == "rendered"
        mock_render.assert_called_once_with("admin/backup/index.html", backups=[])


def test_backup_create_redirects_after_backup(app):
    with patch.object(backup_module, "create_backup_file", return_value=("backup.zip", "/tmp/backup.zip")), patch.object(backup_module, "cleanup_old_backups") as mock_cleanup, patch.object(backup_module, "flash") as mock_flash, patch.object(backup_module, "redirect", return_value="redirected") as mock_redirect, patch.object(backup_module, "url_for", return_value="/admin/manage/backup"):
        result = backup_module.backup_create()

        assert result == "redirected"
        mock_flash.assert_called_once()
        mock_cleanup.assert_called_once_with(limit=10)


def test_backup_download_missing_file_redirects(app):
    with app.test_request_context("/admin/manage/backup/download/missing.zip"):
        with patch("lib.routes.admin.manage.backup.os.path.exists", return_value=False), patch.object(backup_module, "redirect", return_value="redirected") as mock_redirect, patch.object(backup_module, "url_for", return_value="/admin/manage/backup"):
            result = backup_module.backup_download("missing.zip")

            assert result == "redirected"


def test_backup_delete_removes_existing_file(app):
    with patch("lib.routes.admin.manage.backup.os.path.exists", return_value=True), patch("lib.routes.admin.manage.backup.os.remove") as mock_remove, patch.object(backup_module, "flash") as mock_flash, patch.object(backup_module, "redirect", return_value="redirected") as mock_redirect, patch.object(backup_module, "url_for", return_value="/admin/manage/backup"):
        result = backup_module.backup_delete("backup.zip")

        assert result == "redirected"
        mock_remove.assert_called_once()
        mock_flash.assert_called_once()


def test_upload_remote_backup_success(app, tmp_path):
    """Test successful remote backup upload"""
    backup_file = tmp_path / "test_backup.zip"
    backup_file.write_text("test content")
    
    with patch.object(backup_module, "BACKUP_DIR", str(tmp_path)), \
         patch("lib.routes.admin.manage.backup.os.path.exists", return_value=True), \
         patch("lib.routes.admin.manage.backup.RemoteBackupHandler") as mock_handler_class:
        
        mock_handler = MagicMock()
        mock_handler.upload_backup.return_value = {
            'scp': [(True, 'SCP upload successful')],
            'ftp': [(True, 'FTP upload successful')],
            'https': [(True, 'HTTPS upload successful')]
        }
        mock_handler_class.return_value = mock_handler
        
        with app.test_request_context("/admin/manage/backup/api/upload-remote/test_backup.zip", method="POST"):
            result = backup_module.upload_remote_backup("test_backup.zip")
            
            assert result.status_code == 200
            data = result.get_json()
            assert data['success'] is True
            assert 'results' in data


def test_upload_remote_backup_file_not_found(app):
    """Test remote upload when backup file doesn't exist"""
    with patch("lib.routes.admin.manage.backup.os.path.exists", return_value=False):
        with app.test_request_context("/admin/manage/backup/api/upload-remote/missing.zip", method="POST"):
            result = backup_module.upload_remote_backup("missing.zip")
            
            # Returns a tuple (response, status_code)
            response, status_code = result
            assert status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert 'not found' in data['message']
