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
            assert config['SESSION_COOKIE_SECURE'] is False
            assert config['SESSION_COOKIE_HTTPONLY'] is True
            assert config['SESSION_COOKIE_SAMESITE'] == 'Lax'
            assert config['MAX_CONTENT_LENGTH'] == 52428800


def test_get_config_production_requires_secret_key():
    """Test that production mode fails without SECRET_KEY."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True):
            with pytest.raises(ValueError):
                SecureConfig.get_config(tmpdir)


def test_csrf_generate_token():
    """Test CSRF token generation."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    with app.test_request_context():
        session.clear()
        token1 = CSRFProtection.generate_token()
        token2 = CSRFProtection.generate_token()
        assert token1 == token2  # Same session
        assert len(token1) == 64


def test_csrf_validate_token_valid():
    """Test CSRF token validation with valid token."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    with app.test_request_context():
        session.clear()
        token = CSRFProtection.generate_token()
        assert CSRFProtection.validate_token(token) is True


def test_csrf_validate_token_invalid():
    """Test CSRF token validation with invalid token."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    with app.test_request_context():
        session.clear()
        CSRFProtection.generate_token()
        assert CSRFProtection.validate_token('invalid-token') is False


def test_csrf_validate_token_no_session():
    """Test CSRF token validation without session token."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    with app.test_request_context():
        session.clear()
        assert CSRFProtection.validate_token('any-token') is False


@patch('lib.security.secure_config.abort')
@patch('lib.security.secure_config.security_logger')
def test_csrf_require_csrf_valid(mock_logger, mock_abort):
    """Test CSRF decorator with valid token."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    
    @app.route('/test', methods=['POST'])
    @CSRFProtection.require_csrf
    def test_route():
        return 'ok'
    
    with app.test_request_context('/test', method='POST', data={'_csrf_token': 'valid'}):
        session['_csrf_token'] = 'valid'
        response = test_route()
        assert response == 'ok'
        mock_abort.assert_not_called()


@patch('lib.security.secure_config.abort')
@patch('lib.security.secure_config.security_logger')
def test_csrf_require_csrf_invalid(mock_logger, mock_abort):
    """Test CSRF decorator with invalid token."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'
    
    @app.route('/test', methods=['POST'])
    @CSRFProtection.require_csrf
    def test_route():
        return 'forbidden'
    
    with app.test_request_context('/test', method='POST', data={'_csrf_token': 'invalid'}):
        session['_csrf_token'] = 'valid'
        response = test_route()
        mock_abort.assert_called_once_with(403)
        mock_logger.warning.assert_called_once()


def test_csrf_require_csrf_get_request():
    """Test CSRF decorator allows GET requests."""
    app = Flask(__name__)
    
    @app.route('/test')
    @CSRFProtection.require_csrf
    def test_route():
        return 'ok'
    
    with app.test_request_context('/test', method='GET'):
        response = test_route()
        assert response == 'ok'


def test_csrf_require_csrf_header_token_valid():
    """Test CSRF decorator accepts X-CSRF-Token header."""
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'

    @app.route('/test', methods=['POST'])
    @CSRFProtection.require_csrf
    def test_route():
        return 'ok'

    with app.test_request_context('/test', method='POST', headers={'X-CSRF-Token': 'valid'}):
        session['_csrf_token'] = 'valid'
        response = test_route()
        assert response == 'ok'


@patch('lib.security.secure_config.security_logger')
def test_security_logger_failed_login(mock_logger):
    """Test logging failed login."""
    SecurityLogger.log_failed_login('testuser', '192.168.1.1')
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert 'testuser' in call_args
    assert '192.168.1.1' in call_args


@patch('lib.security.secure_config.security_logger')
def test_security_logger_rate_limit(mock_logger):
    """Test logging rate limit exceeded."""
    SecurityLogger.log_rate_limit_exceeded('/api/test', '10.0.0.1')
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args[0][0]
    assert '/api/test' in call_args
    assert '10.0.0.1' in call_args


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


def test_file_upload_validator_invalid_extension():
    """Test file upload validation rejects disallowed extensions."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage

    file = FileStorage(
        stream=BytesIO(b'test content'),
        filename='malware.exe',
        content_type='application/octet-stream'
    )

    is_valid, msg = FileUploadValidator.validate_upload(file, category='images')
    assert not is_valid
    assert 'not allowed' in msg.lower()


def test_file_upload_validator_too_large():
    """Test file upload validation rejects files over max size."""
    from io import BytesIO
    from werkzeug.datastructures import FileStorage

    content = b'a' * (FileUploadValidator.MAX_FILENAME_LENGTH + 1)
    file = FileStorage(
        stream=BytesIO(content),
        filename='test.jpg',
        content_type='image/jpeg'
    )

    is_valid, msg = FileUploadValidator.validate_upload(file, category='images', max_size=10)
    assert not is_valid
    assert 'too large' in msg.lower()


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
