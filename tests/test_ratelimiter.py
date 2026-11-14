import os
import json
import time
import tempfile

import pytest
from flask import Flask

from lib.security.ratelimiter import RateLimiter, rate_limit


def test_rate_limiter_blocks_after_max_requests():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir, max_requests=2, window_seconds=60)
        assert limiter.is_rate_limited('test-ip') is False
        assert limiter.is_rate_limited('test-ip') is False
        assert limiter.is_rate_limited('test-ip') is True


def test_rate_limiter_cleans_old_entries():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir, max_requests=1, window_seconds=1)
        assert limiter.is_rate_limited('cleanup-ip') is False
        assert limiter.is_rate_limited('cleanup-ip') is True

        # Wait for the window to expire and cleanup_old_data to remove the entry
        time.sleep(1.1)
        limiter.cleanup_old_data()
        assert limiter.is_rate_limited('cleanup-ip') is False


def test_login_lockout_and_reset():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir)
        username = 'user@example.com'

        # Initially not locked
        locked, _ = limiter.check_login_attempt(username)
        assert locked is False

        # Record failed attempts to trigger lockout
        for _ in range(5):
            limiter.record_failed_login(username, max_attempts=5, lockout_duration=1)

        locked, message = limiter.check_login_attempt(username)
        assert locked is True
        assert 'locked' in message

        # Wait for lockout to expire
        time.sleep(1.1)
        locked, _ = limiter.check_login_attempt(username)
        assert locked is False

        # Reset attempts explicitly
        limiter.record_failed_login(username, max_attempts=5, lockout_duration=1)
        limiter.reset_login_attempts(username)
        locked, _ = limiter.check_login_attempt(username)
        assert locked is False


def test_lockout_does_not_extend_while_account_is_already_blocked():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir)
        username = 'locked-user@example.com'

        limiter.record_failed_login(username, max_attempts=1, lockout_duration=2)
        first_lock_until = limiter._load_lockouts()[username]['locked_until']

        time.sleep(0.1)
        limiter.record_failed_login(username, max_attempts=1, lockout_duration=2)
        second_lock_until = limiter._load_lockouts()[username]['locked_until']

        assert second_lock_until == first_lock_until
        assert limiter.check_login_attempt(username)[0] is True


def test_lockout_expiration_resets_failed_attempt_counter():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir)
        username = 'reset-after-expiration@example.com'

        limiter.record_failed_login(username, max_attempts=2, lockout_duration=1)
        limiter.record_failed_login(username, max_attempts=2, lockout_duration=1)
        assert limiter.check_login_attempt(username)[0] is True

        time.sleep(1.1)
        limiter.record_failed_login(username, max_attempts=2, lockout_duration=1)

        lockout_state = limiter._load_lockouts()[username]
        assert lockout_state['attempts'] == 1
        assert lockout_state['locked_until'] is None


def test_rate_limiter_file_fallback_persists_state_and_handles_expired_lockouts():
    with tempfile.TemporaryDirectory() as temp_dir:
        limiter = RateLimiter(temp_dir, max_requests=2, window_seconds=1)
        username = 'file-fallback-user@example.com'

        assert limiter.is_rate_limited('file-fallback-ip') is False
        assert limiter.is_rate_limited('file-fallback-ip') is False
        assert limiter.is_rate_limited('file-fallback-ip') is True

        limiter.record_failed_login(username, max_attempts=2, lockout_duration=1)
        limiter.record_failed_login(username, max_attempts=2, lockout_duration=1)
        assert limiter.check_login_attempt(username)[0] is True

        time.sleep(1.1)
        assert limiter.check_login_attempt(username)[0] is False
        assert limiter._load_lockouts()[username]['attempts'] == 0


def test_rate_limit_decorator_aborts_when_limit_reached():
    with tempfile.TemporaryDirectory() as temp_dir:
        app = Flask(__name__)
        app.root_path = temp_dir

        @app.route('/limited')
        @rate_limit(max_requests=1, window_seconds=60)
        def limited():
            return 'ok'

        with app.test_client() as client:
            assert client.get('/limited').status_code == 200
            assert client.get('/limited').status_code == 429


def test_rate_limit_decorator_uses_custom_key_func():
    with tempfile.TemporaryDirectory() as temp_dir:
        app = Flask(__name__)
        app.root_path = temp_dir

        @app.route('/custom')
        @rate_limit(max_requests=1, window_seconds=60, key_func=lambda: 'custom-key')
        def custom_limited():
            return 'ok'

        with app.test_client() as client:
            assert client.get('/custom').status_code == 200
            assert client.get('/custom').status_code == 429
