import json
import os
from flask import Flask, Response
from lib.security.headers import (
    add_security_headers,
    validate_input,
    sanitize_filename,
    InputValidator,
)


def test_validate_input_removes_unsafe_characters():
    value = '<script>alert(1)</script>& test'
    sanitized = validate_input(value)
    assert '<' not in sanitized
    assert '>' not in sanitized
    assert '&' not in sanitized
    assert 'script' in sanitized


def test_validate_input_rejects_too_long():
    long_value = 'x' * 1001
    assert validate_input(long_value, max_length=1000) is None


def test_sanitize_filename_removes_path_traversal():
    safe = sanitize_filename('../../etc/passwd')
    assert safe != '../../etc/passwd'
    assert '..' not in safe
    assert '/' not in safe


def test_sanitize_filename_limits_length():
    long_name = 'a' * 300 + '.txt'
    safe = sanitize_filename(long_name, max_length=100)
    assert len(safe) <= 100
    assert safe.endswith('.txt')


def test_add_security_headers_sets_expected_headers():
    app = Flask(__name__)
    app.config['TESTING'] = True
    add_security_headers(app)

    @app.route('/')
    def index():
        return 'ok'

    client = app.test_client()
    response = client.get('/')

    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'
    assert 'Strict-Transport-Security' not in response.headers
    assert 'Content-Security-Policy' in response.headers
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert 'Permissions-Policy' in response.headers


def test_add_security_headers_sets_hsts_on_https():
    app = Flask(__name__)
    app.config['TESTING'] = True
    add_security_headers(app)

    @app.route('/')
    def index():
        return 'ok'

    client = app.test_client()
    response = client.get('/', base_url='https://localhost')

    assert response.headers['Strict-Transport-Security'] == 'max-age=31536000; includeSubDomains'


def test_input_validator_email_username_password_url_integer():
    assert InputValidator.validate_email('user@example.com') is True
    assert InputValidator.validate_email('bad-email') is False
    assert InputValidator.validate_username('user_123') is True
    assert InputValidator.validate_username('no spaces') is False
    ok, msg = InputValidator.validate_password('Abcdef12')
    assert ok is True
    assert 'strong' in msg.lower()
    assert InputValidator.validate_password('weak') == (False, 'Password must be at least 8 characters long')
    assert InputValidator.validate_url('https://example.com/path') is True
    assert InputValidator.validate_url('ftp://example.com') is False
    assert InputValidator.validate_integer('5', min_val=1, max_val=10) is True
    assert InputValidator.validate_integer('20', min_val=1, max_val=10) is False
    assert InputValidator.validate_integer('not-a-number') is False


def test_validate_input_valid_string():
    """Test validate_input with valid string."""
    result = validate_input("hello world")
    assert result == "hello world"


def test_validate_input_none():
    """Test validate_input with None."""
    result = validate_input(None)
    assert result is None


def test_validate_input_non_string():
    """Test validate_input with non-string."""
    result = validate_input(123)
    assert result is None


def test_validate_input_too_long():
    """Test validate_input with string too long."""
    long_string = "a" * 1001
    result = validate_input(long_string)
    assert result is None


def test_validate_input_max_length():
    """Test validate_input with max length."""
    string = "a" * 1000
    result = validate_input(string)
    assert result == string


def test_validate_input_custom_max_length():
    """Test validate_input with custom max length."""
    result = validate_input("hello", max_length=3)
    assert result is None
    
    result = validate_input("hi", max_length=3)
    assert result == "hi"


def test_validate_input_allowed_chars():
    """Test validate_input with allowed_chars restriction."""
    # When allowed_chars is provided, dangerous chars in that list are not removed
    result = validate_input("hello<>", allowed_chars=['<', '>'])
    assert result == "hello<>"  # < and > are not removed because in allowed_chars
    
    result = validate_input("hello", allowed_chars=[])
    assert result == "hello"


def test_validate_input_empty_allowed_chars():
    """Test validate_input with empty allowed_chars."""
    result = validate_input("hello", allowed_chars=[])
    assert result == "hello"  # Empty list means no restriction


def test_validate_input_newlines_and_tabs():
    """Test validate_input preserves newlines and tabs."""
    input_str = "hello\nworld\t!"
    result = validate_input(input_str)
    assert result == input_str


def test_validate_input_unicode():
    """Test validate_input with unicode characters."""
    input_str = "héllo wörld"
    result = validate_input(input_str)
    assert result == input_str


def test_validate_input_empty_string():
    """Test validate_input with empty string."""
    result = validate_input("")
    assert result is None  # Empty string returns None


def test_validate_input_only_dangerous():
    """Test validate_input with string containing only dangerous chars."""
    result = validate_input("<>\"'&;")
    assert result is None  # All chars removed, then returns None for empty
