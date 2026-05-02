# Security Architecture Diagram

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    INTERNET / CLOUDFLARE TUNNEL                  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                         FLASK APPLICATION                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    ProxyFix Middleware                      │ │
│  │  (X-Forwarded-Proto, X-Forwarded-For handling)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Security Headers Middleware                    │ │
│  │  • X-Frame-Options: SAMEORIGIN                             │ │
│  │  • CSP: Strict Content Security Policy                     │ │
│  │  • HSTS: Force HTTPS                                       │ │
│  │  • X-XSS-Protection: Enable browser XSS filter             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Rate Limiting Middleware                       │ │
│  │  • Check IP against rate_limits.json                       │ │
│  │  • 300 req/min (general), 100 req/min (admin)              │ │
│  │  • Return 429 if exceeded                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Route Handlers                            │ │
│  │                                                             │ │
│  │  /login (POST)                                             │ │
│  │  ├─ Input Validation (username, password)                  │ │
│  │  ├─ Check lockouts.json (brute force protection)           │ │
│  │  ├─ Verify credentials                                     │ │
│  │  ├─ Reset lockout on success                               │ │
│  │  └─ Record failure, update lockout on fail                 │ │
│  │                                                             │ │
│  │  /register (POST)                                          │ │
│  │  ├─ Input Validation (email, username, password)           │ │
│  │  ├─ Strong password check (8+ chars, mixed case)           │ │
│  │  ├─ Rate limit by IP                                       │ │
│  │  └─ Create user with encrypted storage                     │ │
│  │                                                             │ │
│  │  /admin/* (Protected)                                      │ │
│  │  ├─ Require admin role                                     │ │
│  │  ├─ Rate limit per endpoint                                │ │
│  │  └─ Validate all inputs                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            Transparent Encryption Layer                     │ │
│  │  (EncryptedFileManager)                                     │ │
│  │                                                             │ │
│  │  • Intercepts all file read/write operations                │ │
│  │  • Checks if .encryption_enabled flag exists                │ │
│  │  • Automatically encrypts on write                          │ │
│  │  • Automatically decrypts on read                           │ │
│  │  • Backward compatible with plaintext                       │ │
│  │                                                             │ │
│  │  Flow: Request → Validation → File Operation               │ │
│  │                     ↓                                       │ │
│  │           EncryptedFileManager                              │ │
│  │                     ↓                                       │ │
│  │           Encryption Check                                 │ │
│  │            / Yes       \ No                                 │ │
│  │           ↓             ↓                                   │ │
│  │        Fernet          PlainText                            │ │
│  │       Encrypt           Write                               │ │
│  │           \             /                                   │ │
│  │            ↓           ↓                                    │ │
│  │          File Storage                                       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              ↓                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              File Storage (Encrypted)                       │ │
│  │                                                             │ │
│  │  ├─ settings.json ──→ [🔒 Encrypted Binary]               │ │
│  │  ├─ users.json ─────→ [🔒 Encrypted Binary]               │ │
│  │  ├─ analytics.json ─→ [🔒 Encrypted Binary]               │ │
│  │  ├─ comments.json ──→ [🔒 Encrypted Binary]               │ │
│  │  ├─ .encryption_key (Fernet Key - 44 bytes)               │ │
│  │  └─ .encryption_enabled (Control Flag)                    │ │
│  │                                                             │ │
│  │  ├─ rate_limits.json (JSON - tracks IP requests)           │ │
│  │  └─ lockouts.json (JSON - tracks login attempts)           │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Encryption Flow Detail

```
┌─────────────────────────────────────────────────────────────┐
│                    READ OPERATION                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. AuthManager._load() called                             │
│     ↓                                                      │
│  2. Get EncryptionManager                                  │
│     ↓                                                      │
│  3. Check if file encrypted                               │
│     / Encrypted       \ Not encrypted                      │
│    ↓                  ↓                                     │
│  4a. load_json_file() 4b. Plain read                       │
│   (with decrypt)       & json.load()                       │
│     ↓                  ↓                                    │
│  5. Fernet.decrypt()   ↓                                    │
│     ↓                  ↓                                    │
│  6. json.loads()  ←────┘                                    │
│     ↓                                                      │
│  7. Return data dict                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    WRITE OPERATION                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. AuthManager._save(data) called                         │
│     ↓                                                      │
│  2. json.dumps(data) → JSON string                         │
│     ↓                                                      │
│  3. Check if encryption enabled                           │
│     / Enabled         \ Disabled                           │
│    ↓                  ↓                                     │
│  4a. Fernet.encrypt()  4b. Plain write                     │
│     ↓                  ↓                                    │
│  5a. Binary data   ←───┘                                    │
│     ↓                                                      │
│  6. Write to file                                          │
│     ↓                                                      │
│  7. Done                                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Authentication Flow with Security

```
┌────────────────────────────────────────────────────────────┐
│                    LOGIN ATTEMPT                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. User submits login form                               │
│     ├─ Username: "admin"                                  │
│     └─ Password: "SecurePass123"                          │
│                                                            │
│  2. InputValidator checks format                          │
│     ├─ Username: 3-32 alphanumeric ✓                      │
│     └─ Password: not empty ✓                              │
│                                                            │
│  3. Check login rate limits (per IP)                      │
│     ├─ IP 192.168.1.1: 5/100 requests ✓                   │
│     └─ Continue                                           │
│                                                            │
│  4. Check account lockout (in lockouts.json)              │
│     ├─ Admin:                                             │
│     │  └─ attempts: 0, locked_until: null ✓               │
│     └─ Continue                                           │
│                                                            │
│  5. Load users.json (auto-decrypted)                      │
│     ├─ Read encrypted file                                │
│     ├─ Fernet.decrypt() with key                          │
│     └─ json.loads() → user data                           │
│                                                            │
│  6. Verify credentials                                    │
│     ├─ Get admin hash with salt                           │
│     ├─ Hash(password + salt)                              │
│     ├─ Compare hashes ✓                                   │
│     └─ Match!                                             │
│                                                            │
│  7. Success: Reset lockout counter                        │
│     ├─ lockouts_data["admin"] = {attempts: 0}             │
│     └─ Save (auto-encrypted)                              │
│                                                            │
│  8. Set secure session cookie                             │
│     ├─ Secure: HTTPS only                                 │
│     ├─ HttpOnly: No JS access                             │
│     ├─ SameSite: Lax (CSRF protection)                    │
│     └─ Expire: 1 hour                                     │
│                                                            │
│  9. Redirect to dashboard                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    FAILED LOGIN                            │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Same as above, but at step 6:                            │
│                                                            │
│  6. Verify credentials                                    │
│     ├─ Hashes don't match ✗                               │
│     └─ FAILED                                             │
│                                                            │
│  7. Record failed attempt                                 │
│     ├─ lockouts_data["admin"]["attempts"] += 1            │
│     ├─ Current: 4 → 5 (LOCKOUT TRIGGERED!)                │
│     ├─ lockouts_data["admin"]["locked_until"] = now+300s  │
│     └─ Save (auto-encrypted)                              │
│                                                            │
│  8. Return error to client                                │
│     └─ "Account locked for 300 seconds"                   │
│                                                            │
│  9. Subsequent attempts get 429 Too Many Requests         │
│                                                            │
│  10. After 5 minutes (300s), lockout expires              │
│      └─ User can try again                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Rate Limiting Flow

```
┌──────────────────────────────────────────────────────────┐
│            REQUEST ARRIVES AT check_rate_limits()        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Extract client IP                                   │
│     ├─ From request.remote_addr                         │
│     └─ Or X-Forwarded-For header (via ProxyFix)         │
│                                                          │
│  2. Determine limit category                            │
│     ├─ /static, /uploads     → 1000 req/min             │
│     ├─ /admin/*              → 100 req/min              │
│     └─ Others                → 300 req/min              │
│                                                          │
│  3. Check rate_limits.json                              │
│     ├─ Load request history for IP                      │
│     ├─ Remove old requests (>60s old)                   │
│     ├─ Count remaining requests                         │
│     └─ Current: 298, Limit: 300 ✓                       │
│                                                          │
│  4a. Within limit: Continue ✓                           │
│     ├─ Add current timestamp to history                 │
│     ├─ Save updated history                             │
│     └─ Process request normally                         │
│                                                          │
│  4b. Exceeded limit: Return 429                         │
│     ├─ Log: "Rate limit exceeded for IP 192.168.1.1"    │
│     ├─ Return HTTP 429 Too Many Requests                │
│     ├─ Show error page                                  │
│     └─ Request never reaches handler                    │
│                                                          │
│  5. Automatic cleanup (hourly)                          │
│     ├─ Background thread runs                           │
│     ├─ Removes data older than 24 hours                 │
│     ├─ Keeps file from growing indefinitely             │
│     └─ Doesn't block requests                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Input Validation Chain

```
┌──────────────────────────────────────────────────────────┐
│            FORM SUBMISSION /register                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Raw Input:                                             │
│  ├─ username: "<admin>"                                 │
│  ├─ email: "user@example.com"                           │
│  └─ password: "weak"                                    │
│                                                          │
│  ↓ Validation Chain:                                    │
│                                                          │
│  1. InputValidator.validate_username()                  │
│     ├─ Check: 3-32 alphanumeric + underscore            │
│     ├─ "<admin>" contains '<' and '>'                   │
│     ├─ INVALID ✗                                        │
│     └─ Return: "Invalid username format"                │
│                                                          │
│  [If passed]                                            │
│  2. InputValidator.validate_email()                     │
│     ├─ Check: RFC-compliant format                      │
│     ├─ "user@example.com" matches pattern               │
│     ├─ VALID ✓                                          │
│     └─ Continue                                         │
│                                                          │
│  [If passed]                                            │
│  3. InputValidator.validate_password()                  │
│     ├─ Length: 8+ characters                            │
│     │  └─ "weak" = 4 chars ✗                            │
│     ├─ INVALID ✗                                        │
│     └─ Return: "Password must be 8+ chars"              │
│                                                          │
│  Response: 400 Bad Request                              │
│  └─ "Invalid username format"                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## File Encryption States

```
UNENCRYPTED FILE               ENCRYPTED FILE
─────────────────────────────────────────────────
settings.json                  gAAAAABmAbc...XYZ
(human readable)               (binary gibberish)

{                              Contains:
  "site_title": "Blog",        • Fernet format marker
  "domain": "example.com",     • Initialization vector
  "settings": {...}            • Encrypted data
}                              • Authentication tag

FILE SIZE: ~1 KB               FILE SIZE: ~1.2 KB (+20%)

READABLE BY:                   READABLE BY:
• Text editor ✓                • Text editor ✗
• cat command ✓                • cat command ✗ (garbage)
• Human ✓                      • Human ✗
                               • Only with key + password

REQUIRES:
• None                         • Correct encryption key
                               • Fernet library
```

---

## Security Stack

```
Layer 7 (Application)
├─ Input Validation (InputValidator)
├─ Authentication (AuthManager with lockouts)
├─ Authorization (require_admin decorators)
└─ Output Encoding (Jinja2 templates)

Layer 6 (Presentation)
├─ Security Headers (CSP, HSTS, X-Frame-Options)
├─ Error Handling (Custom error pages)
└─ Session Management (Secure cookies)

Layer 5 (Session/Encryption)
├─ File Encryption (Fernet AES-128)
├─ Key Management (Automatic key generation)
└─ Encryption Control (Enable/disable flag)

Layer 4 (Transport)
├─ ProxyFix (X-Forwarded-Proto handling)
├─ HTTPS (via Cloudflare tunnel)
└─ Certificate Validation

Layer 3 (Network)
├─ Rate Limiting (IP-based)
├─ DDOS Protection (Per-endpoint limits)
└─ Account Lockout (Brute force protection)

Layer 2 (Data)
├─ File Permissions (0600 for key)
├─ Encrypted Storage (AES-128)
└─ Integrity Verification (HMAC)

Layer 1 (Infrastructure)
├─ Access Control (Admin authentication)
├─ Monitoring (Rate limit/lockout logs)
└─ Backup (Encryption key backup)
```

---

**Last Updated:** April 25, 2026  
**Security Architecture Version:** 1.0
