"""
Security utilities for hardened Flask application.
Handles secure configuration, secret key management, CSRF protection, and logging.
"""

import os
import secrets
import logging
from functools import wraps
from flask import request, abort, session
from datetime import datetime

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)

class SecureConfig:
    """Secure configuration manager using environment variables"""
    
    @staticmethod
    def get_secret_key(base_path):
        """
        Get or generate Flask secret key.
        Tries environment variable first, then looks for stored key file,
        generates new one if needed (only in development).
        """
        # Try environment variable first
        secret_key = os.environ.get('SECRET_KEY')
        if secret_key:
            return secret_key
        
        # Try to load from secure key file
        key_file = os.path.join(base_path, 'keys', 'flask_secret_key')
        if os.path.exists(key_file):
            try:
                with open(key_file, 'r') as f:
                    secret_key = f.read().strip()
                    if secret_key and len(secret_key) >= 32:
                        return secret_key
            except Exception as e:
                security_logger.warning(f"Could not read secret key file: {e}")
        
        # Development-only: Generate and store new key
        environment = os.environ.get('FLASK_ENV', 'development')
        if environment == 'development':
            secret_key = secrets.token_hex(32)
            try:
                keys_dir = os.path.join(base_path, 'keys')
                os.makedirs(keys_dir, exist_ok=True)
                with open(key_file, 'w') as f:
                    f.write(secret_key)
                os.chmod(key_file, 0o600)  # Restrict to owner only
            except Exception as e:
                security_logger.error(f"Could not store secret key: {e}")
            return secret_key
        
        # Production: Must have SECRET_KEY environment variable
        raise ValueError(
            "SECRET_KEY environment variable not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    
    @staticmethod
    def get_config(base_path):
        """Get secure Flask configuration"""
        environment = os.environ.get('FLASK_ENV', 'production')
        
        return {
            'SECRET_KEY': SecureConfig.get_secret_key(base_path),
            'DEBUG': environment == 'development' and os.environ.get('FLASK_DEBUG', 'False') == 'True',
            'TESTING': environment == 'testing',
            'SESSION_COOKIE_SECURE': os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True',
            'SESSION_COOKIE_HTTPONLY': os.environ.get('SESSION_COOKIE_HTTPONLY', 'True') == 'True',
            'SESSION_COOKIE_SAMESITE': os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            'PERMANENT_SESSION_LIFETIME': int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)),
            'MAX_CONTENT_LENGTH': int(os.environ.get('MAX_UPLOAD_SIZE', 52428800))  # 50MB default
        }


class CSRFProtection:
    """CSRF token management for forms"""
    
    @staticmethod
    def generate_token():
        """Generate a new CSRF token"""
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return session['_csrf_token']
    
    @staticmethod
    def validate_token(token):
        """Validate CSRF token"""
        if '_csrf_token' not in session:
            return False
        return token == session['_csrf_token']
    
    @staticmethod
    def require_csrf(f):
        """Decorator to require valid CSRF token for POST requests"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
                if not token or not CSRFProtection.validate_token(token):
                    security_logger.warning(f"CSRF validation failed for {request.path} from {request.remote_addr}")
                    abort(403)
            return f(*args, **kwargs)
        return decorated_function


class SecurityLogger:
    """Centralized security event logging"""
    
    @staticmethod
    def log_failed_login(username, ip_address):
        """Log failed login attempt"""
        security_logger.warning(f"Failed login attempt: username={username}, ip={ip_address}, time={datetime.utcnow()}")
    
    @staticmethod
    def log_rate_limit_exceeded(endpoint, ip_address):
        """Log rate limit exceeded"""
        security_logger.warning(f"Rate limit exceeded: endpoint={endpoint}, ip={ip_address}, time={datetime.utcnow()}")
    
    @staticmethod
    def log_unauthorized_access(user, endpoint, ip_address):
        """Log unauthorized access attempt"""
        security_logger.warning(f"Unauthorized access: user={user}, endpoint={endpoint}, ip={ip_address}, time={datetime.utcnow()}")
    
    @staticmethod
    def log_file_upload(username, filename, size, status):
        """Log file upload"""
        security_logger.info(f"File upload: user={username}, file={filename}, size={size}, status={status}, time={datetime.utcnow()}")
    
    @staticmethod
    def log_config_change(username, setting, old_value, new_value):
        """Log configuration changes"""
        security_logger.warning(f"Config changed: user={username}, setting={setting}, old={old_value}, new={new_value}, time={datetime.utcnow()}")
    
    @staticmethod
    def log_privilege_escalation(username, old_role, new_role):
        """Log privilege changes"""
        security_logger.warning(f"Privilege changed: user={username}, old_role={old_role}, new_role={new_role}, time={datetime.utcnow()}")


class FileUploadValidator:
    """Validate file uploads for security"""
    
    MAX_FILENAME_LENGTH = 255
    ALLOWED_EXTENSIONS = {
        'images': {'jpg', 'jpeg', 'png', 'gif', 'ico', 'webp'},
        'documents': {'pdf', 'doc', 'docx', 'txt'},
        'config': {'json', 'html', 'css'},
        'video': {'mp4', 'webm', 'avi', 'wmv', 'mov'},
        'audio': {'mp3', 'wav', 'ogg', 'm4a'}
    }
    
    @staticmethod
    def is_safe_filename(filename):
        """Check if filename is safe"""
        if not filename or len(filename) > FileUploadValidator.MAX_FILENAME_LENGTH:
            return False
        # Don't allow path traversal
        if '..' in filename or filename.startswith('/'):
            return False
        # Don't allow special characters
        if any(char in filename for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']):
            return False
        return True
    
    @staticmethod
    def is_allowed_extension(filename, category='images'):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        allowed = FileUploadValidator.ALLOWED_EXTENSIONS.get(category, set())
        return ext in allowed
    
    @staticmethod
    def validate_upload(file, category='images', max_size=52428800):
        """Validate complete file upload"""
        if not file or file.filename == '':
            return False, "No file selected"
        
        if not FileUploadValidator.is_safe_filename(file.filename):
            return False, "Invalid filename"
        
        if not FileUploadValidator.is_allowed_extension(file.filename, category):
            return False, f"File type not allowed. Allowed types: {', '.join(FileUploadValidator.ALLOWED_EXTENSIONS[category])}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Seek back to start
        
        if size > max_size:
            return False, f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
        
        return True, "Valid"


def sanitize_path(base_dir, requested_path):
    """
    Prevent path traversal attacks.
    Ensures requested path is within base_dir.
    """
    import os.path
    
    # Resolve to absolute paths
    base = os.path.abspath(base_dir)
    target = os.path.abspath(os.path.join(base, requested_path))
    
    # Check if target is within base
    if not target.startswith(base + os.sep):
        raise ValueError(f"Path traversal detected: {requested_path}")
    
    return target
