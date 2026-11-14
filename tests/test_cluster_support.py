import os
import pickle
import socket
import subprocess
import sys
import time

import pytest
from flask import Flask, request

from lib.security.cluster_session import RedisSessionInterface
from lib.security.ratelimiter import RateLimiter

try:
    import fakeredis
except Exception:
    fakeredis = None


def ensure_redis_running(port=6379, db=15):
    if fakeredis is not None:
        return fakeredis.FakeRedis(decode_responses=False)

    pytest.skip("No in-memory Redis-compatible backend is available for the cluster test")


def test_cluster_mode_rate_limiter_is_shared_across_instances():
    redis_client = ensure_redis_running()

    limiter_a = RateLimiter(
        "/tmp/siteforge-cluster-test",
        max_requests=2,
        window_seconds=60,
        redis_url="redis://unused",
        load_balancing_enabled=True,
        namespace="cluster-proof",
        redis_client=redis_client,
    )
    limiter_b = RateLimiter(
        "/tmp/siteforge-cluster-test",
        max_requests=2,
        window_seconds=60,
        redis_url="redis://unused",
        load_balancing_enabled=True,
        namespace="cluster-proof",
        redis_client=redis_client,
    )

    assert limiter_a.is_rate_limited("shared-ip") is False
    assert limiter_b.is_rate_limited("shared-ip") is False
    assert limiter_a.is_rate_limited("shared-ip") is True


def test_cluster_mode_requires_redis_when_enabled():
    with pytest.raises(RuntimeError, match="Redis"):
        RateLimiter(
            "/tmp/siteforge-cluster-test",
            max_requests=2,
            window_seconds=60,
            redis_url="redis://127.0.0.1:65535/0",
            load_balancing_enabled=True,
            namespace="cluster-proof",
        )


def test_redis_session_interface_round_trips_data():
    redis_client = ensure_redis_running()
    app = Flask(__name__)
    app.config["SESSION_COOKIE_NAME"] = "siteforge_session"
    interface = RedisSessionInterface(redis_client=redis_client, prefix="siteforge:session:")

    session_data = {"user_id": "demo-user", "language": "de"}
    redis_client.setex("siteforge:session:test-session", 3600, pickle.dumps(session_data))

    with app.test_request_context("/", headers={"Cookie": "siteforge_session=test-session"}):
        session = interface.open_session(app, request)
        assert session == session_data

    class DummySession(dict):
        sid = "saved-session"

    response = object()
    interface.save_session(app, DummySession({"status": "ok"}), response)
    assert pickle.loads(redis_client.get("siteforge:session:saved-session")) == {"status": "ok"}


def test_redis_backed_rate_limit_state_round_trips():
    redis_client = ensure_redis_running()
    limiter = RateLimiter(
        "/tmp/siteforge-cluster-test",
        max_requests=2,
        window_seconds=60,
        namespace="redis-roundtrip",
        redis_client=redis_client,
    )

    assert limiter.is_rate_limited("redis-user") is False
    assert limiter.is_rate_limited("redis-user") is False

    limiter._save_limits({"redis-user": [1.0, 2.0], "empty-user": []})
    assert limiter._load_limits()["redis-user"] == [1.0, 2.0]

    limiter._save_lockouts({"alice": {"attempts": 2, "locked_until": None}})
    lockouts = limiter._load_lockouts()
    assert lockouts["alice"]["attempts"] == 2
    assert lockouts["alice"]["locked_until"] is None


def test_redis_login_lockout_expires_and_clears():
    redis_client = ensure_redis_running()
    limiter = RateLimiter(
        "/tmp/siteforge-cluster-test",
        max_requests=2,
        window_seconds=60,
        namespace="redis-lockout",
        redis_client=redis_client,
    )

    limiter.record_failed_login("alice@example.com", max_attempts=1, lockout_duration=1)
    locked, message = limiter.check_login_attempt("alice@example.com")
    assert locked is True
    assert "locked" in message.lower()

    time.sleep(1.1)
    locked, _ = limiter.check_login_attempt("alice@example.com")
    assert locked is False
    assert redis_client.exists("redis-lockout:lockout:alice@example.com") == 0


def test_redis_cleanup_removes_stale_entries():
    redis_client = ensure_redis_running()
    limiter = RateLimiter(
        "/tmp/siteforge-cluster-test",
        max_requests=2,
        window_seconds=60,
        namespace="redis-cleanup",
        redis_client=redis_client,
    )

    redis_client.rpush("redis-cleanup:rate:old-user", str(time.time() - 86500))
    redis_client.hset("redis-cleanup:lockout:old-user", mapping={"attempts": "3", "locked_until": str(time.time() - 1)})

    limiter.cleanup_old_data()

    assert redis_client.exists("redis-cleanup:rate:old-user") == 0
    assert redis_client.exists("redis-cleanup:lockout:old-user") == 0
