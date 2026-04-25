"""
Rate limiting and DDOS protection module
"""
import time
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, abort


class RateLimiter:
    """Simple in-memory rate limiter with file persistence"""
    
    def __init__(self, base_path, max_requests=100, window_seconds=60):
        self.base_path = base_path
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.limits_file = os.path.join(base_path, "data", "rate_limits.json")
        self.lockouts_file = os.path.join(base_path, "data", "lockouts.json")
        os.makedirs(os.path.dirname(self.limits_file), exist_ok=True)
        
    def _load_limits(self):
        """Load request tracking data"""
        if os.path.exists(self.limits_file):
            try:
                with open(self.limits_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_limits(self, data):
        """Save request tracking data"""
        try:
            with open(self.limits_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def _load_lockouts(self):
        """Load account lockouts"""
        if os.path.exists(self.lockouts_file):
            try:
                with open(self.lockouts_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_lockouts(self, data):
        """Save account lockouts"""
        try:
            with open(self.lockouts_file, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def is_rate_limited(self, identifier):
        """Check if identifier has exceeded rate limit"""
        limits = self._load_limits()
        now = time.time()
        
        if identifier not in limits:
            limits[identifier] = []
        
        # Remove old requests outside the window
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
        limiter = RateLimiter(self.base_path, max_requests=max_requests, window_seconds=window_seconds)
        return limiter.is_rate_limited(f"ip_{ip_address}")
    
    def check_endpoint_limit(self, endpoint, max_requests=100, window_seconds=60):
        """Rate limit by endpoint"""
        limiter = RateLimiter(self.base_path, max_requests=max_requests, window_seconds=window_seconds)
        return limiter.is_rate_limited(f"endpoint_{endpoint}")
    
    def check_login_attempt(self, username, max_attempts=5):
        """Track failed login attempts and lockout after N failures"""
        lockouts = self._load_lockouts()
        now = time.time()
        
        if username not in lockouts:
            lockouts[username] = {"attempts": 0, "locked_until": None}
        
        # Check if account is locked
        locked_until = lockouts[username].get("locked_until")
        if locked_until and now < locked_until:
            remaining = int(locked_until - now)
            return True, f"Account locked for {remaining} more seconds"
        
        # Reset if lock has expired
        if locked_until and now >= locked_until:
            lockouts[username] = {"attempts": 0, "locked_until": None}
        
        return False, None
    
    def record_failed_login(self, username, max_attempts=5, lockout_duration=300):
        """Record failed login and apply lockout after N attempts"""
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
        lockouts = self._load_lockouts()
        if username in lockouts:
            lockouts[username] = {"attempts": 0, "locked_until": None}
            self._save_lockouts(lockouts)
    
    def cleanup_old_data(self):
        """Clean up old tracking data (call periodically)"""
        limits = self._load_limits()
        lockouts = self._load_lockouts()
        now = time.time()
        
        # Clean up limits older than 24 hours
        for key in list(limits.keys()):
            limits[key] = [
                req_time for req_time in limits[key]
                if now - req_time < 86400
            ]
            if not limits[key]:
                del limits[key]
        
        # Clean up expired lockouts
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
            
            # Determine the identifier key
            if key_func:
                identifier = key_func()
            else:
                identifier = request.remote_addr
            
            base_path = current_app.root_path
            limiter = RateLimiter(base_path, max_requests=max_requests, window_seconds=window_seconds)
            
            if limiter.is_rate_limited(identifier):
                abort(429)  # Too Many Requests
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
