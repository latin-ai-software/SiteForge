# Security Features - Quick Setup Guide

## What Was Implemented

### 1. **DDOS Protection (Rate Limiting)**
- IP-based rate limiting to prevent attack flooding
- Configurable limits per endpoint type
- Automatic cleanup of old data

### 2. **Account Lockout**
- 5 failed login attempts = 5-minute lockout
- Prevents brute force attacks
- Tracks attempts per username

### 3. **Strong Password Policy**
- Minimum 8 characters
- Requires uppercase, lowercase, and digits
- Enforced on registration and password changes

### 4. **Security Headers**
- HSTS (HTTPS enforcement)
- CSP (XSS prevention)
- X-Frame-Options (clickjacking prevention)
- More...

### 5. **Input Validation**
- Email validation
- Username format checking
- File upload type/size validation
- XSS character removal
- Path traversal prevention

---

## Quick Start

### 1. Verify Installation
All security modules are already imported in `app.py`. No additional packages needed (using built-in Flask/Werkzeug).

### 2. Test Rate Limiting
```bash
# Try 10 rapid login attempts (should lock out after 5)
for i in {1..10}; do
  curl -X POST http://localhost:443/login \
    -d "username=admin&password=wrong"
  echo "Attempt $i"
done
# After 5th attempt, should see: "Account locked for X more seconds"
```

### 3. Test Security Headers
```bash
# Check if security headers are present
curl -I https://your-domain.com
# Look for headers like X-Frame-Options, Content-Security-Policy, etc.
```

### 4. Monitor Rate Limits
```bash
# View current rate limits
cat data/rate_limits.json

# View account lockouts  
cat data/lockouts.json
```

---

## Configuration Options

### Adjust Rate Limits
Edit `lib/security/ratelimiter.py`:

```python
# Change default limits
RateLimiter(base_path, max_requests=100, window_seconds=60)

# In app.py, check_rate_limits() function:
# General endpoints: 300 requests/minute
# Admin endpoints: 100 requests/minute
# Static files: 1000 requests/minute
```

### Adjust Lockout Duration
Edit `lib/routes/root/auth.py`:

```python
# Change lockout from 5 min (300 sec) to something else
rate_limiter.record_failed_login(username, max_attempts=5, lockout_duration=300)
```

### Adjust Password Requirements
Edit `lib/security/headers.py` in `InputValidator.validate_password()`:

```python
if len(password) < 8:  # Change minimum length
    return False, "Password must be at least 8 characters long"
```

---

## Monitoring & Maintenance

### Daily Checks
```bash
# Monitor for suspicious activity
tail -f data/lockouts.json

# Check for rate limit abuse patterns
jq '.[] | select(length > 100)' data/rate_limits.json
```

### Weekly Tasks
```bash
# Backup security data
cp data/rate_limits.json data/rate_limits.json.backup
cp data/lockouts.json data/lockouts.json.backup

# Review admin logs
grep "Rate limit exceeded" /var/log/flask.log
```

### Security Headers Verification
Visit https://securityheaders.com/ and enter your domain to verify all headers are correctly set.

---

## File Locations

| Component | File |
|-----------|------|
| Rate Limiter | `lib/security/ratelimiter.py` |
| Validators | `lib/security/headers.py` |
| Auth Routes | `lib/routes/root/auth.py` |
| App Config | `app.py` |
| Error Template | `templates/error.html` |
| Documentation | `SECURITY.md` |

---

## Troubleshooting

### Getting "Too Many Requests" (429)
- This means rate limit was exceeded
- Wait for timeout period (usually 1 minute)
- Or clear `data/rate_limits.json` (dev only)

### Account Locked
- User exceeded failed login attempts
- Wait 5 minutes or admin can clear `data/lockouts.json`
- User will see: "Account locked for X more seconds"

### HTTPS Issues  
- Mixed content error? Check [HTTPS proxy setup](../SECURITY.md#9-httpsproxy-configuration)
- `window.location.origin` is used to auto-detect protocol
- ProxyFix middleware handles X-Forwarded-Proto

### Rate Limits Too Strict
- Adjust thresholds in `app.py` `check_rate_limits()` function
- Increase max_requests values as needed
- Remember to restart Flask after changes

---

## Production Recommendations

### 1. Change Secret Key
```python
# In app.py, generate a new secret
import secrets
print(secrets.token_urlsafe(32))
# Replace the hardcoded secret in app.py
```

### 2. Enable HTTPS
```bash
# Using Let's Encrypt + certbot
sudo certbot certonly -d your-domain.com
# Update Flask to use SSL context
```

### 3. Monitor Logs
```bash
# Set up log aggregation (e.g., with journalctl)
journalctl -u latinmagazine -f
```

### 4. Database Backups
```bash
# Backup rate limit and lockout data daily
0 2 * * * cp /app/data/rate_limits.json /backups/rate_limits.json.$(date +%Y%m%d)
```

### 5. Update Dependencies
```bash
# Regularly update Flask and security packages
pip list --outdated
pip install --upgrade werkzeug flask
```

---

## Support

For detailed information, see [SECURITY.md](../SECURITY.md)

For questions, review:
- `lib/security/ratelimiter.py` - Rate limiting logic
- `lib/security/headers.py` - Validation & headers  
- `lib/routes/root/auth.py` - Authentication flow
- `app.py` - Global configuration

---

**Last Updated:** April 25, 2026  
**Security Version:** 1.0
