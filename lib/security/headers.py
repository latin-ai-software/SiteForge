"""
Security headers middleware
"""
from flask import request


def add_security_headers(app):
    """Add security headers to all responses"""
    
    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection in older browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (replaces Feature-Policy)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Strict Transport Security (HSTS) - only if HTTPS
        if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy - strict but allows inline for legacy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://cdn.quilljs.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.quilljs.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: https: i.ytimg.com; "
            "font-src 'self' data:; "
            "connect-src 'self' https://www.google-analytics.com; "
            "frame-ancestors 'self'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        return response


def validate_input(data, max_length=1000, allowed_chars=[]):
    """
    Validate and sanitize user input
    
    Args:
        data: Input string to validate
        max_length: Maximum allowed length
        allowed_chars: Set of allowed characters (None = allow all printable)
    
    Returns:
        Sanitized string or None if invalid
    """
    if not isinstance(data, str):
        return None
    
    # Check length
    if len(data) > max_length:
        return None
    
    # Basic XSS prevention - remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';']
    for char in dangerous_chars:
        if char in data and not (char == '&' and '&amp;' in data) and char not in allowed_chars:
            data = data.replace(char, '')
    
    return data.strip() if data else None


def sanitize_filename(filename, max_length=255):
    """
    Sanitize filename to prevent directory traversal
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
    
    Returns:
        Sanitized filename
    """
    from werkzeug.utils import secure_filename
    
    # Use werkzeug's secure_filename
    safe = secure_filename(filename)
    
    # Additional checks
    if not safe or safe == '.' or safe == '..':
        return 'file'
    
    # Remove leading/trailing dots
    safe = safe.strip('.')
    
    # Limit length
    if len(safe) > max_length:
        name, ext = safe.rsplit('.', 1) if '.' in safe else (safe, '')
        safe = name[:max_length-len(ext)-1] + '.' + ext if ext else safe[:max_length]
    
    return safe


class InputValidator:
    """Comprehensive input validation"""
    
    @staticmethod
    def validate_email(email):
        """Validate email address"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) and len(email) < 255
    
    @staticmethod
    def validate_username(username):
        """Validate username (alphanumeric + underscore, 3-32 chars)"""
        import re
        pattern = r'^[a-zA-Z0-9_]{3,32}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password):
        """
        Validate password strength
        - Minimum 8 characters (configurable)
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and digits"
        
        return True, "Password is strong"
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        import re
        pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=-]*)?$'
        return bool(re.match(pattern, url)) and len(url) < 2048
    
    @staticmethod
    def validate_integer(value, min_val=None, max_val=None):
        """Validate integer within range"""
        try:
            num = int(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False
