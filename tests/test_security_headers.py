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


def test_add_security_headers_on_response():
    app = Flask(__name__)
    add_security_headers(app)

    @app.route('/test')
    def test_route():
        return Response('ok')

    client = app.test_client()
    response = client.get('/test', base_url='https://localhost')
    assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert 'X-XSS-Protection' in response.headers
    assert response.headers['Referrer-Policy'] == 'strict-origin-when-cross-origin'
    assert response.headers['Permissions-Policy'].startswith('geolocation=()')
    assert response.headers['Strict-Transport-Security'] == 'max-age=31536000; includeSubDomains'
    assert 'Content-Security-Policy' in response.headers
