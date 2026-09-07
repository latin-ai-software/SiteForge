"""
Rate limiting and DDOS protection module
"""
import json
import os
import time
from datetime import datetime, timedelta
from functools import wraps

import redis
from flask import abort, jsonify, request


class RateLimiter:
    """Distributed rate limiter with file fallback for single-node deployments."""

    def __init__(
        self,
        base_path,
        max_requests=100,
        window_seconds=60,
        redis_url=None,
        load_balancing_enabled=False,
        namespace="siteforge",
        redis_client=None,
    ):
        self.base_path = base_path
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_url = redis_url or os.environ.get("REDIS_URL") or os.environ.get("SITEFORGE_REDIS_URL") or "redis://localhost:6379/0"
        self.load_balancing_enabled = bool(load_balancing_enabled or str(os.environ.get("LOAD_BALANCING_ENABLED", "false")).lower() in {"1", "true", "yes", "on"})
        self.namespace = namespace
        self.limits_file = os.path.join(base_path, "data", "rate_limits.json")
        self.lockouts_file = os.path.join(base_path, "data", "lockouts.json")
        os.makedirs(os.path.dirname(self.limits_file), exist_ok=True)

        self._redis = redis_client
        if self.load_balancing_enabled and self._redis is None:
            self._redis = redis.Redis.from_url(self.redis_url, decode_responses=True)
            try:
                self._redis.ping()
            except Exception as exc:
                raise RuntimeError(
                    "Redis is required when load balancing is enabled. Set REDIS_URL to a reachable Redis instance or start Redis before enabling cluster mode."
                ) from exc

    def _rate_key(self, identifier):
        return f"{self.namespace}:rate:{identifier}"

    def _lockout_key(self, username):
        return f"{self.namespace}:lockout:{username}"

    def _load_limits(self):
        if self._redis is not None:
            data = {}
            for key in self._redis.scan_iter(match=f"{self.namespace}:rate:*"):
                values = [float(v) for v in self._redis.lrange(key, 0, -1) if v]
                if values:
                    data[key.replace(f"{self.namespace}:rate:", "")] = values
            return data
        if os.path.exists(self.limits_file):
            try:
                with open(self.limits_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_limits(self, data):
        if self._redis is not None:
            for key_name, values in list(data.items()):
                redis_key = self._rate_key(key_name)
                if values:
                    pipeline = self._redis.pipeline()
                    pipeline.delete(redis_key)
                    if values:
                        pipeline.rpush(redis_key, *[str(v) for v in values])
                    pipeline.expire(redis_key, self.window_seconds)
                    pipeline.execute()
                else:
                    self._redis.delete(redis_key)
            existing_keys = set(self._redis.scan_iter(match=f"{self.namespace}:rate:*"))
            for key in existing_keys:
                if key not in {self._rate_key(k) for k in data.keys()}:
                    self._redis.delete(key)
            return
        try:
            with open(self.limits_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _load_lockouts(self):
        if self._redis is not None:
            data = {}
            for key in self._redis.scan_iter(match=f"{self.namespace}:lockout:*"):
                payload = self._redis.hgetall(key)
                if payload:
                    data[key.replace(f"{self.namespace}:lockout:", "")] = {
                        "attempts": int(payload.get("attempts", 0)),
                        "locked_until": float(payload["locked_until"]) if payload.get("locked_until") else None,
                    }
            return data
        if os.path.exists(self.lockouts_file):
            try:
                with open(self.lockouts_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_lockouts(self, data):
        if self._redis is not None:
            for username, payload in list(data.items()):
                redis_key = self._lockout_key(username)
                self._redis.delete(redis_key)
                if payload:
                    self._redis.hset(redis_key, mapping={
                        "attempts": str(payload.get("attempts", 0)),
                        "locked_until": str(payload.get("locked_until")) if payload.get("locked_until") is not None else "",
                    })
                    self._redis.expire(redis_key, max(300, int(self.window_seconds * 2)))
            existing_keys = set(self._redis.scan_iter(match=f"{self.namespace}:lockout:*"))
            for key in existing_keys:
                if key not in {self._lockout_key(k) for k in data.keys()}:
                    self._redis.delete(key)
            return
        try:
            with open(self.lockouts_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def is_rate_limited(self, identifier):
        """Check if identifier has exceeded rate limit"""
        if self._redis is not None:
            key = self._rate_key(identifier)
            now = time.time()
            entries = [float(v) for v in self._redis.lrange(key, 0, -1) if v]
            entries = [req_time for req_time in entries if now - req_time < self.window_seconds]
            if len(entries) >= self.max_requests:
                if entries:
                    self._redis.ltrim(key, 0, len(entries) - 1)
                    self._redis.expire(key, self.window_seconds)
                return True
            entries.append(now)
            self._redis.delete(key)
            if entries:
                self._redis.rpush(key, *[str(v) for v in entries])
            self._redis.expire(key, self.window_seconds)
            return False

        limits = self._load_limits()
        now = time.time()

        if identifier not in limits:
            limits[identifier] = []

        limits[identifier] = [
            req_time for req_time in limits[identifier]
            if now - req_time < self.window_seconds
        ]

        is_limited = len(limits[identifier]) >= self.max_requests

        if not is_limited:
            limits[identifier].append(now)

        self._save_limits(limits)
        return is_limited

    def check_ip_limit(self, ip_address, max_requests=200, window_seconds=60):
        """Rate limit by IP address (DDOS protection)"""
        limiter = RateLimiter(self.base_path, max_requests=max_requests, window_seconds=window_seconds, redis_url=self.redis_url, load_balancing_enabled=self.load_balancing_enabled, namespace=self.namespace)
        return limiter.is_rate_limited(f"ip_{ip_address}")

    def check_endpoint_limit(self, endpoint, max_requests=100, window_seconds=60):
        """Rate limit by endpoint"""
        limiter = RateLimiter(self.base_path, max_requests=max_requests, window_seconds=window_seconds, redis_url=self.redis_url, load_balancing_enabled=self.load_balancing_enabled, namespace=self.namespace)
        return limiter.is_rate_limited(f"endpoint_{endpoint}")

    def check_login_attempt(self, username, max_attempts=5):
        """Track failed login attempts and lockout after N failures"""
        if self._redis is not None:
            payload = self._redis.hgetall(self._lockout_key(username))
            if not payload:
                return False, None
            locked_until = float(payload["locked_until"]) if payload.get("locked_until") else None
            now = time.time()
            if locked_until and now < locked_until:
                remaining = int(locked_until - now)
                return True, f"Account locked for {remaining} more seconds"
            if locked_until and now >= locked_until:
                self._redis.delete(self._lockout_key(username))
                return False, None
            return False, None

        lockouts = self._load_lockouts()
        now = time.time()

        if username not in lockouts:
            lockouts[username] = {"attempts": 0, "locked_until": None}

        locked_until = lockouts[username].get("locked_until")
        if locked_until and now < locked_until:
            remaining = int(locked_until - now)
            return True, f"Account locked for {remaining} more seconds"

        if locked_until and now >= locked_until:
            lockouts[username] = {"attempts": 0, "locked_until": None}

        return False, None

    def record_failed_login(self, username, max_attempts=5, lockout_duration=300):
        """Record failed login and apply lockout after N attempts"""
        if self._redis is not None:
            payload = self._redis.hgetall(self._lockout_key(username)) or {"attempts": "0", "locked_until": ""}
            attempts = int(payload.get("attempts", 0)) + 1
            now = time.time()
            locked_until = None
            if attempts >= max_attempts:
                locked_until = now + lockout_duration
            self._redis.hset(self._lockout_key(username), mapping={
                "attempts": str(attempts),
                "locked_until": str(locked_until) if locked_until is not None else "",
            })
            self._redis.expire(self._lockout_key(username), max(300, int(lockout_duration + 60)))
            return

        lockouts = self._load_lockouts()
        now = time.time()

        if username not in lockouts:
            lockouts[username] = {"attempts": 0, "locked_until": None}

        lockouts[username]["attempts"] += 1

        if lockouts[username]["attempts"] >= max_attempts:
            lockouts[username]["locked_until"] = now + lockout_duration

        self._save_lockouts(lockouts)

    def reset_login_attempts(self, username):
        """Reset login attempts after successful login"""
        if self._redis is not None:
            self._redis.delete(self._lockout_key(username))
            return

        lockouts = self._load_lockouts()
        if username in lockouts:
            lockouts[username] = {"attempts": 0, "locked_until": None}
            self._save_lockouts(lockouts)

    def cleanup_old_data(self):
        """Clean up old tracking data (call periodically)"""
        if self._redis is not None:
            now = time.time()
            for key in self._redis.scan_iter(match=f"{self.namespace}:rate:*"):
                values = [float(v) for v in self._redis.lrange(key, 0, -1) if v]
                values = [value for value in values if now - value < 86400]
                if values:
                    self._redis.delete(key)
                    self._redis.rpush(key, *[str(v) for v in values])
                    self._redis.expire(key, 86400)
                else:
                    self._redis.delete(key)
            for key in self._redis.scan_iter(match=f"{self.namespace}:lockout:*"):
                payload = self._redis.hgetall(key)
                locked_until = float(payload.get("locked_until")) if payload.get("locked_until") else None
                if locked_until and now >= locked_until:
                    self._redis.delete(key)
            return

        limits = self._load_limits()
        lockouts = self._load_lockouts()
        now = time.time()

        for key in list(limits.keys()):
            limits[key] = [
                req_time for req_time in limits[key]
                if now - req_time < 86400
            ]
            if not limits[key]:
                del limits[key]

        for key in list(lockouts.keys()):
            locked_until = lockouts[key].get("locked_until")
            if locked_until and now >= locked_until:
                del lockouts[key]

        self._save_limits(limits)
        self._save_lockouts(lockouts)


def rate_limit(max_requests=100, window_seconds=60, key_func=None):
    """Decorator for rate limiting endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import current_app

            if key_func:
                identifier = key_func()
            else:
                identifier = request.remote_addr

            base_path = current_app.root_path
            limiter = RateLimiter(
                base_path,
                max_requests=max_requests,
                window_seconds=window_seconds,
                redis_url=current_app.config.get("REDIS_URL"),
                load_balancing_enabled=current_app.config.get("LOAD_BALANCING_ENABLED", False),
                namespace=current_app.config.get("LOAD_BALANCING_NAMESPACE", "siteforge"),
            )

            if limiter.is_rate_limited(identifier):
                abort(429)

            return f(*args, **kwargs)

        return decorated_function
    return decorator
