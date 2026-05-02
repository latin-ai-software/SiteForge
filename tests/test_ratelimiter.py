import os
import json
import time
import tempfile
from lib.security.ratelimiter import RateLimiter


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
