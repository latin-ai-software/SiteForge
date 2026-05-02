import pytest
import json
import os
from unittest.mock import patch, MagicMock
from lib.routes.admin.manage.remote_backup import RemoteBackupHandler


@pytest.fixture
def temp_backup_dir(tmp_path):
    """Create temporary backup directory structure"""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create settings file
    settings_file = data_dir / "settings.json"
    settings_file.write_text(json.dumps({
        'backup_scp_enabled': True,
        'backup_scp_host': 'backup.example.com',
        'backup_scp_port': 22,
        'backup_scp_user': 'backupuser',
        'backup_scp_password': 'password',
        'backup_scp_remote_path': '/backups/',
        'backup_ftp_enabled': True,
        'backup_ftp_host': 'ftp.example.com',
        'backup_ftp_port': 21,
        'backup_ftp_user': 'ftpuser',
        'backup_ftp_password': 'ftppass',
        'backup_ftp_remote_path': '/backups/',
        'backup_https_enabled': True,
        'backup_https_url': 'https://backup.example.com/upload',
        'backup_https_token': 'secret-token-123'
    }))
    
    # Create test backup file
    backup_file = backup_dir / "test_backup.zip"
    backup_file.write_text("test backup content")
    
    return tmp_path, str(tmp_path)


def test_load_remote_settings_success(temp_backup_dir):
    """Test loading remote settings from settings file"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    settings = handler.load_remote_settings()
    
    assert settings['scp_enabled'] is True
    assert settings['scp_host'] == 'backup.example.com'
    assert settings['ftp_enabled'] is True
    assert settings['https_enabled'] is True


def test_load_remote_settings_no_file(tmp_path):
    """Test loading remote settings when no file exists"""
    handler = RemoteBackupHandler(str(tmp_path))
    settings = handler.load_remote_settings()
    
    assert settings == {}


def test_upload_via_scp_not_configured(temp_backup_dir):
    """Test SCP upload when host not configured"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    success, message = handler.upload_via_scp("/tmp/backup.zip", {'scp_host': ''})
    
    assert success is False
    assert "not configured" in message


def test_upload_via_ftp_not_configured(temp_backup_dir):
    """Test FTP upload when host not configured"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    success, message = handler.upload_via_ftp("/tmp/backup.zip", {'ftp_host': ''})
    
    assert success is False
    assert "not configured" in message


def test_upload_via_https_not_configured(temp_backup_dir):
    """Test HTTPS upload when URL not configured"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    success, message = handler.upload_via_https("/tmp/backup.zip", {'https_url': ''})
    
    assert success is False
    assert "not configured" in message


def test_get_configured_destinations(temp_backup_dir):
    """Test getting list of configured destinations"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    destinations = handler.get_configured_destinations()
    
    assert len(destinations) == 3
    types = [d['type'] for d in destinations]
    assert 'SCP' in types
    assert 'FTP' in types
    assert 'HTTPS' in types


def test_get_configured_destinations_partial(tmp_path):
    """Test getting configured destinations with only some enabled"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    settings_file = data_dir / "settings.json"
    settings_file.write_text(json.dumps({
        'backup_scp_enabled': True,
        'backup_scp_host': 'backup.example.com',
        'backup_scp_port': 22,
        'backup_ftp_enabled': False,
        'backup_https_enabled': False
    }))
    
    handler = RemoteBackupHandler(str(tmp_path))
    destinations = handler.get_configured_destinations()
    
    assert len(destinations) == 1
    assert destinations[0]['type'] == 'SCP'


def test_get_configured_destinations_none_enabled(tmp_path):
    """Test getting configured destinations with none enabled"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    settings_file = data_dir / "settings.json"
    settings_file.write_text(json.dumps({
        'backup_scp_enabled': False,
        'backup_ftp_enabled': False,
        'backup_https_enabled': False
    }))
    
    handler = RemoteBackupHandler(str(tmp_path))
    destinations = handler.get_configured_destinations()
    
    assert len(destinations) == 0


def test_upload_backup_uses_configured_destinations(temp_backup_dir):
    """Test upload_backup method structure"""
    _, base_path = temp_backup_dir
    handler = RemoteBackupHandler(base_path)
    
    with patch.object(handler, 'upload_via_scp', return_value=(True, "success")) as mock_scp, \
         patch.object(handler, 'upload_via_ftp', return_value=(True, "success")) as mock_ftp, \
         patch.object(handler, 'upload_via_https', return_value=(True, "success")) as mock_https:
        
        backup_file = os.path.join(base_path, "backups", "test_backup.zip")
        results = handler.upload_backup(backup_file)
        
        # Should return dictionary with protocol keys
        assert 'scp' in results
        assert 'ftp' in results
        assert 'https' in results
        
        # With our test settings, all protocols are enabled
        mock_scp.assert_called_once()
        mock_ftp.assert_called_once()
        mock_https.assert_called_once()
