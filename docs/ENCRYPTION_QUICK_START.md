# Encryption System - Quick Start

## What's New

Your configuration files are now **automatically encrypted** using military-grade AES-128 encryption with authentication. This includes:

- User accounts & password hashes
- Site settings & API keys
- Analytics data
- Comments & metadata

---

## Installation

### 1. Install Required Package

```bash
pip install cryptography
```

Or update your environment:

```bash
pip install -r requirements.txt
```

### 2. Initialize Encryption

On first run, the system automatically:
- Generates a unique encryption key
- Creates control flags
- **Encryption is active by default**

---

## Verify It's Working

### Check Status

```bash
python test_encryption.py status
```

Output:
```
CURRENT ENCRYPTION STATUS
==============================================================

Encryption System: ENABLED ✓

Configuration Files:
--------------------------------------------------------------
  settings.json                  🔒 ENCRYPTED   1024 bytes
  users.json                     🔒 ENCRYPTED    512 bytes
  analytics.json                 🔒 ENCRYPTED   2048 bytes
--------------------------------------------------------------

Encryption Key: Present (44 bytes)
Key Location: data/.encryption_key
```

### Run Full Test Suite

```bash
python test_encryption.py test
```

Should see:
```
Test 1: Importing encryption modules...
  ✓ All modules imported successfully

Test 2: Creating temporary test environment...
  ✓ Encryption manager initialized

Test 3: Verifying encryption key...
  ✓ Valid Fernet key generated (44 bytes)

Test 4: Testing encryption/decryption...
  ✓ Data encrypted (144 bytes)
  ✓ Data decrypted successfully and matches original

...

✓ ALL TESTS PASSED - Encryption system is working!
```

---

## Backup Your Encryption Key

**CRITICAL:** Without the backup, encrypted files are **unrecoverable**.

### Create Backup

```bash
python encrypt_config.py backup
```

This creates:
- `data/.encryption_key.backup_20260425_120000` (file copy)
- Displays key in Base64 format (for manual backup)

**Save the Base64 string to:**
- Password manager (LastPass, 1Password, Bitwarden)
- Encrypted cloud storage (Tresorit, Sync.com)
- Secure physical location (encrypted USB, safe)

### Example Backup Output

```
✓ Key backed up to: data/.encryption_key.backup_20260425_120000
  Key size: 44 bytes
  Backup file size: 44 bytes

📋 SAVE THIS BACKUP SAFELY:
--------------------------------------------------------------
gAAAAABmAbc1234567890abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJ==
--------------------------------------------------------------

Store this backup in a secure location!
```

---

## View Encrypted Files

Encrypted files look like binary gibberish:

```bash
# Don't try this - it's encrypted!
cat data/users.json

# Output: gAAAAABmAbc1234567890abcdefghijklmnop...
```

The app automatically decrypts when needed. **Never edit encrypted files directly.**

---

## Manage Encryption

### Via Admin Panel

1. Go to `/admin/settings/`
2. Look for "Encryption" section
3. Click "Check Status", "Enable", or "Disable"

### Via CLI

```bash
# Check status
python encrypt_config.py status

# Enable encryption
python encrypt_config.py enable

# Disable encryption (caution!)
python encrypt_config.py disable

# Backup key
python encrypt_config.py backup

# Restore key
python encrypt_config.py restore "gAAAAABmAbc1234567890..."
```

---

## Key Operations

### 1. Enable (Default)

Encrypts all configuration files:

```bash
python encrypt_config.py enable
```

### 2. Disable (Not Recommended)

Decrypts all files (for migration/troubleshooting):

```bash
python encrypt_config.py disable
```

⚠️ **Warning:** Leaves files readable as plain text!

### 3. Backup

Creates encrypted key backup:

```bash
python encrypt_config.py backup
```

### 4. Restore

Restores encryption key from backup:

```bash
python encrypt_config.py restore "gAAAAABm..."
```

### 5. Rotate Key

Securely generate a new key:

```bash
# 1. Backup current key
python encrypt_config.py backup

# 2. Disable (decrypt with old key)
python encrypt_config.py disable

# 3. Remove old key
rm data/.encryption_key

# 4. Re-enable (generates new key)
python encrypt_config.py enable

# 5. Backup new key
python encrypt_config.py backup
```

---

## File Locations

| Component | Location |
|-----------|----------|
| Encryption Key | `data/.encryption_key` |
| Control Flag | `data/.encryption_enabled` |
| Key Backups | `data/.encryption_key.backup_*` |
| Encrypted Files | `data/*.json` |

---

## Troubleshooting

### Error: "Failed to decrypt data - invalid encryption key"

**Solution:** Restore from backup

```bash
python encrypt_config.py restore "backup-key-here"
```

### Error: "Encryption manager not initialized"

**Solution:** Restart the Flask app

```bash
# If using Cloudflared tunnel:
python app.py

# Or with your deployment method
```

### Files won't encrypt

**Solution:** Check permissions

```bash
chmod 600 data/.encryption_key
```

### Lost the encryption key!

**Solution:** You must restore from backup

```bash
# If you saved the Base64 backup
python encrypt_config.py restore "gAAAAABm..."

# If you have the backup file
cp data/.encryption_key.backup_20260425_120000 data/.encryption_key
```

If you have NO backup: Files are unrecoverable. Reinstall with fresh data.

---

## Integration with Your App

### Automatic Encryption

All file operations automatically use encryption:

```python
# These all work transparently!
from lib.security.encrypted_files import load_encrypted_json, save_encrypted_json

# Load (auto-decrypts if encrypted)
config = load_encrypted_json("data/settings.json")

# Modify
config["new_setting"] = "value"

# Save (auto-encrypts if enabled)
save_encrypted_json("data/settings.json", config)
```

### Transparent in Existing Code

AuthManager, FileManager, and other modules automatically handle encryption. **No code changes needed.**

---

## Security Notes

✅ **Encrypted:**
- All JSON configuration files
- User passwords (still hashed + salted)
- Site settings and API keys
- Analytics data

❌ **NOT Encrypted:**
- Source code
- Static files (CSS, JS, images)
- Application logs
- Network traffic (use HTTPS for that)

---

## Performance

- **Overhead:** ~1-5ms per file operation
- **File size:** ~20% larger (authentication data)
- **CPU impact:** Negligible (hardware-accelerated)

---

## Support

For detailed information, see:
- [ENCRYPTION.md](ENCRYPTION.md) - Complete guide
- [SECURITY.md](SECURITY.md) - Overall security
- `python encrypt_config.py --help` - CLI help

---

**That's it!** Your files are now encrypted and you're all set. Remember to **backup the encryption key**!
