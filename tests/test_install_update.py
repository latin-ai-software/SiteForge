import os
import json
import tempfile
import zipfile
from unittest.mock import patch, MagicMock
from updater.install_update import install_update


def make_zip_bytes(file_map):
    import io
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zf:
        for path, content in file_map.items():
            zf.writestr(path, content)
    return buffer.getvalue()


def test_install_update_success_creates_files_and_logs():
    with tempfile.TemporaryDirectory() as base_path:
        data_dir = os.path.join(base_path, 'data')
        os.makedirs(data_dir, exist_ok=True)
        version_json = {
            'requires_update': True,
            'latest_version': '0.1.0',
            'current_version': '0.0.1'
        }
        with open(os.path.join(data_dir, 'version.json'), 'w', encoding='utf-8') as f:
            json.dump(version_json, f)

        # Create a fake package file to install
        update_files = {
            'lib/new_file.txt': 'hello world',
            'README.md': 'updated readme'
        }
        zip_content = make_zip_bytes(update_files)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = zip_content
        mock_response.raise_for_status = MagicMock()

        with patch('updater.install_update.requests.get', return_value=mock_response):
            result = install_update(base_path, 'FAKE-KEY', '0.0.1')

        assert result is True
        assert os.path.exists(os.path.join(base_path, 'lib', 'new_file.txt'))
        assert os.path.exists(os.path.join(base_path, 'README.md'))

        with open(os.path.join(data_dir, 'version.json'), 'r', encoding='utf-8') as f:
            updated_version = json.load(f)
        assert updated_version['requires_update'] is False
        assert updated_version['current_version'] == updated_version['latest_version']

        update_log_path = os.path.join(data_dir, 'update_log.json')
        assert os.path.exists(update_log_path)
        with open(update_log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        assert isinstance(logs, list)
        assert logs[-1]['files_installed'] == len(update_files)


def test_install_update_fails_when_base_path_missing():
    result = install_update('/does/not/exist', 'FAKE-KEY', '0.0.1')
    assert result is False
