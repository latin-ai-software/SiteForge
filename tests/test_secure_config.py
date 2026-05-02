import pytest
import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from flask import Flask, session
from lib.security.secure_config import SecureConfig, CSRFProtection, SecurityLogger, FileUploadValidator


def test_get_secret_key_from_environment():
    """Test getting secret key from environment"""
    with patch.dict(os.environ, {'SECRET_KEY': 'test-secret-key-123'}):
        key = SecureConfig.get_secret_key('/tmp')
        assert key == 'test-secret-key-123'


def test_get_secret_key_generates_in_development():
    """Test that secret key is generated in development"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=False):
            key = SecureConfig.get_secret_key(tmpdir)
            assert len(key) >= 32
            assert key.isalnum()


def test_get_secret_key_from_file():
    """Test reading secret key from file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        keys_dir = os.path.join(tmpdir, 'keys')
        os.makedirs(keys_dir)
        key_file = os.path.join(keys_dir, 'flask_secret_key')
        test_key = 'a' * 64
        with open(key_file, 'w') as f:
            f.write(test_key)
        
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=False):
            key = SecureConfig.get_secret_key(tmpdir)
            assert key == test_key


def test_get_config_returns_dict():
    """Test that get_config returns proper configuration dict"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {'SECRET_KEY': 'test-key'}, clear=False):
            config = SecureConfig.get_config(tmpdir)
            assert isinstance(config, dict)
            assert 'SECRET_KEY' in config
            assert 'DEBUG' in config
            assert 'SESSION_COOKIE_HTTPONLY' in config


def test_csrf_generate_and_validate():
    """Test CSRF token generation and validation"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    
    with app.app_context():
        with app.test_request_context():
            # Generate token
            token = CSRFProtection.generate_token()
            assert isinstance(token, str)
            assert len(token) > 0
            
            # Validate token
            is_valid = CSRFProtection.validate_token(token)
            assert is_valid is True


def test_csrf_reject_invalid_token():
    """Test that invalid CSRF tokens are rejected"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    
    with app.app_context():
        with app.test_request_context():
            CSRFProtection.generate_token()
            is_valid = CSRFProtection.validate_token('invalid-token')
            assert is_valid is False


def test_security_logger_methods():
    """Test that SecurityLogger methods don't crash"""
    with patch('lib.security.secure_config.security_logger') as mock_logger:
        SecurityLogger.log_failed_login('user@example.com', '127.0.0.1')
        assert mock_logger.warning.called
        
        SecurityLogger.log_rate_limit_exceeded('/api/endpoint', '127.0.0.1')
        assert mock_logger.warning.called
        
        SecurityLogger.log_unauthorized_access('user1', '/admin/settings', '127.0.0.1')
        assert mock_logger.warning.called
        
        SecurityLogger.log_file_upload('user1', 'photo.jpg', 1024, 'success')
        assert mock_logger.info.called
        
        SecurityLogger.log_config_change('admin', 'site_title', 'Old', 'New')
        assert mock_logger.warning.called
        
        SecurityLogger.log_privilege_escalation('user1', 'user', 'admin')
        assert mock_logger.warning.called


def test_file_upload_validator_extensions():
    """Test file upload extension validation"""
    # Test allowed images
    assert FileUploadValidator.is_allowed_extension('photo.jpg', 'images') is True
    assert FileUploadValidator.is_allowed_extension('image.png', 'images') is True
    
    # Test disallowed images
    assert FileUploadValidator.is_allowed_extension('script.exe', 'images') is False
    assert FileUploadValidator.is_allowed_extension('doc.pdf', 'images') is False


def test_file_upload_validator_safe_filename():
    """Test safe filename validation"""
    assert FileUploadValidator.is_safe_filename('photo.jpg') is True
    assert FileUploadValidator.is_safe_filename('document_v2.pdf') is True
    
    # Test path traversal
    assert FileUploadValidator.is_safe_filename('../../etc/passwd') is False
    assert FileUploadValidator.is_safe_filename('/etc/passwd') is False
    
    # Test special characters
    assert FileUploadValidator.is_safe_filename('file*.txt') is False
    assert FileUploadValidator.is_safe_filename('file:name.txt') is False


def test_file_upload_validator_complete_validation():
    """Test complete file upload validation"""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage
    
    # Create mock file
    file = FileStorage(
        stream=BytesIO(b'test content'),
        filename='test.jpg',
        content_type='image/jpeg'
    )
    
    is_valid, msg = FileUploadValidator.validate_upload(file, category='images')
    assert is_valid is True
    assert 'Valid' in msg


def test_sanitize_path_prevents_traversal():
    """Test path traversal prevention"""
    from lib.security.secure_config import sanitize_path
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Safe path should work
        safe = sanitize_path(tmpdir, 'subdir/file.txt')
        assert tmpdir in safe
        
        # Traversal should raise error
        with pytest.raises(ValueError):
            sanitize_path(tmpdir, '../../etc/passwd')


def test_csrf_require_decorator():
    """Test CSRF protection decorator"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    
    @app.route('/protected', methods=['POST'])
    @CSRFProtection.require_csrf
    def protected():
        return {'status': 'ok'}
    
    client = app.test_client()
    
    # POST without CSRF token should be rejected
    with app.test_request_context():
        response = client.post('/protected')
        # Will get 403 because no CSRF token
        assert response.status_code in [403, 400]
