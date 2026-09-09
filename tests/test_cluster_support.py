import os
import socket
import subprocess
import sys
import time

import pytest

from lib.security.ratelimiter import RateLimiter

try:
    import fakeredis
except Exception:
    fakeredis = None


def ensure_redis_running(port=6379, db=15):
    if fakeredis is not None:
        return fakeredis.FakeRedis(decode_responses=True)

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
