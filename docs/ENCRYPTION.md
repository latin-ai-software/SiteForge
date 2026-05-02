# Configuration File Encryption Guide

## Overview

All configuration files are now automatically encrypted using **Fernet symmetric encryption** from the `cryptography` library. This provides:

- ✅ **AES-128** encryption with authentication
- ✅ **Automatic transparent encryption/decryption**
- ✅ **Data integrity verification** (prevents tampering)
- ✅ **Key rotation support**
- ✅ **Backward compatible** (can work unencrypted if needed)

---

## Files Protected

The following configuration files are encrypted:

- `data/settings.json` - Site settings
- `data/users.json` - User accounts & password hashes
- `data/analytics.json` - Visitor analytics
- `data/comments.json` - Post comments
- `data/posts_metadata.json` - Post metadata

---

## Architecture

### Encryption Flow

```
User Request
    ↓
AuthManager / FileManager
    ↓
EncryptedFileManager (transparent wrapper)
    ↓
EncryptionManager (encrypt/decrypt)
    ↓
Encrypted File (on disk)
```

### Key Management

- **Key Location**: `data/.encryption_key`
- **Key Format**: Base64-encoded Fernet key (44 bytes)
- **Auto-generated**: Yes, on first startup
- **Permissions**: Read-only (0600) on Unix-like systems

### Encryption Control

- **Control Flag**: `data/.encryption_enabled`
- **When present**: Encryption is active
- **When absent**: All files treated as plaintext
- **Can toggle**: Yes, via admin panel or CLI

---

## How It Works

### 1. Automatic Transparency

Once enabled, all file operations automatically encrypt/decrypt:

```python
# From AuthManager:
def _load(self):
    """Automatically decrypts if file is encrypted"""
    encryption_mgr = self._get_encryption_manager()
    if encryption_mgr:
        return encryption_mgr.load_json(self.userfile)
    # Fallback to plain read

def _save(self, data):
    """Automatically encrypts if enabled"""
    encryption_mgr = self._get_encryption_manager()
    if encryption_mgr:
        encryption_mgr.save_json(self.userfile, data)
    # Fallback to plain write
```

### 2. File Format

**Plaintext file:**
```json
{
  "admin": {
    "password": "hash...",
    "role": "administrator"
  }
}
```

**Encrypted file:**
```
gAAAAABmAbc1234567890abcdef...encrypted_binary_data...
```

The encrypted data is **not readable as text**.

---

## Management

### Via Admin Panel

Navigate to `/admin/settings/` for encryption controls:

```
GET  /admin/settings/encryption/status    - Check current status
POST /admin/settings/encryption/enable    - Enable encryption
POST /admin/settings/encryption/disable   - Disable encryption
```

### Via CLI (encrypt_config.py)

```bash
# Check status
python encrypt_config.py status

# Enable encryption
python encrypt_config.py enable

# Disable encryption (DANGEROUS)
python encrypt_config.py disable

# Backup encryption key
python encrypt_config.py backup

# Restore encryption key
python encrypt_config.py restore <key>
```

---

## Getting Started

### 1. Initial Setup

On first startup, the system automatically:
- Generates a new encryption key: `data/.encryption_key`
- Creates control flag: `data/.encryption_enabled`
- Encryption is **active by default**

### 2. Enable Encryption (if not active)

**Via CLI:**
```bash
python encrypt_config.py enable
```

**Via Admin Panel:**
1. Go to Settings
2. Find "Encryption" section
3. Click "Enable Encryption"
4. Wait for operation to complete

**Result:**
```
✓ Encryption enabled for 5 files
✓ Your data is now protected
```

### 3. Backup Your Key

**CRITICAL:** Backup your encryption key!

**Via CLI:**
```bash
python encrypt_config.py backup
```

This creates:
- `data/.encryption_key.backup_20260425_120000`
- Displays key in Base64 format
- Save the Base64 string securely (LastPass, 1Password, paper, etc.)

**Key output example:**
```
gAAAAABmAbc1234567890abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJ==
```

---

## Backup & Restore

### Scenario 1: Regular Backup

```bash
# Create backup
python encrypt_config.py backup

# Copy backup file to secure location
cp data/.encryption_key.backup_* /secure/location/
```

### Scenario 2: Key Recovery

If you lose your key or need to restore:

```bash
# Option A: Use backup file
cp /secure/location/.encryption_key.backup_* data/.encryption_key

# Option B: Use CLI restore
python encrypt_config.py restore "gAAAAABmAbc1234567890abcdef..."
```

### Scenario 3: Key Rotation

```bash
# 1. Backup current key
python encrypt_config.py backup

# 2. Disable encryption (decrypts files)
python encrypt_config.py disable

# 3. Delete old key
rm data/.encryption_key

# 4. Re-enable (generates new key)
python encrypt_config.py enable

# 5. Backup new key
python encrypt_config.py backup
```

---

## Troubleshooting

### Error: "Failed to decrypt data - invalid encryption key"

**Cause:** Wrong key or corrupted data

**Solution:**
```bash
# Check backup
python encrypt_config.py status

# Restore from backup
python encrypt_config.py restore "gAAAAABm..."
```

### Error: "File not found"

**Cause:** Configuration file missing

**Solution:**
```bash
# Check which files exist
python encrypt_config.py status

# The system auto-creates missing files
# Just restart Flask
```

### Application won't start after encryption

**Cause:** Encryption manager initialization failed

**Solution:**
```bash
# Check permissions
ls -la data/.encryption_key

# Should be: -rw------- (0600)
# Fix permissions
chmod 600 data/.encryption_key

# Restart Flask
```

### Can't read encrypted files manually

**Cause:** Files are encrypted, can't read as text

**Solution:**
```bash
# Use the CLI to check status
python encrypt_config.py status

# Or disable encryption to read files
python encrypt_config.py disable
```

---

## Security Considerations

### ✅ What's Protected

- All configuration file contents
- User password hashes (still hashed + salted)
- Site settings
- Analytics data
- Comments metadata

### ⚠️ What's NOT Protected

- Encryption key itself (protect `data/.encryption_key`)
- Files in static, uploads, media directories (optional separate encryption)
- Application source code
- Web server logs
- Network traffic (use HTTPS for that)

### 🔐 Security Best Practices

1. **Protect the key file**
   ```bash
   # Permissions should be 0600 (owner read/write only)
   chmod 600 data/.encryption_key
   ```

2. **Backup the key securely**
   - Use a password manager (LastPass, 1Password)
   - Store on encrypted USB drive
   - Use cloud backup with encryption (Tresorit, Sync.com)
   - NOT in version control, NOT on plain text emails

3. **Regular key rotation**
   - Every 90-180 days recommended
   - Use the rotation process above

4. **Monitor access**
   - Check file permissions regularly
   - Monitor for unauthorized access attempts
   - Use log aggregation

5. **Disaster recovery plan**
   - Document encryption key location
   - Test restore process quarterly
   - Store recovery procedures securely

---

## Performance Impact

- **Encryption overhead**: ~1-5ms per file operation
- **File size increase**: ~20% (due to authentication data)
- **Memory usage**: Minimal (keys cached in memory)
- **CPU impact**: Negligible (hardware-accelerated)

---

## Advanced Configuration

### Disable Encryption (Not Recommended)

```bash
# Emergency: Decrypt all files
python encrypt_config.py disable

# This will:
# - Decrypt all config files
# - Remove encryption enabled flag
# - Allow plain-text file reading
```

### Custom Encryption Paths

Edit `lib/security/encryption.py` `ConfigEncryption.config_files`:

```python
self.config_files = [
    os.path.join(base_path, "data", "settings.json"),
    os.path.join(base_path, "data", "users.json"),
    # Add custom paths here
    os.path.join(base_path, "data", "custom.json"),
]
```

### Multi-Key Support (Advanced)

To support multiple encryption keys for different files:

1. Extend `EncryptionManager` to support key index
2. Store key index in encrypted file header
3. Implement key rotation logic

(See `ENCRYPTION_ADVANCED.md` for details)

---

## API Reference

### EncryptionManager

```python
from lib.security import EncryptionManager

mgr = EncryptionManager(base_path)

# Encrypt/decrypt data
encrypted = mgr.encrypt_data({"key": "value"})
decrypted = mgr.decrypt_data(encrypted)

# File operations
mgr.encrypt_file("path/to/file.json")
mgr.decrypt_file("path/to/file.json")

# Check status
is_enabled = mgr.is_enabled()
is_encrypted = mgr.is_file_encrypted("file.json")

# Enable/disable
mgr.enable_encryption()
mgr.disable_encryption()
```

### ConfigEncryption

```python
from lib.security import ConfigEncryption

cfg = ConfigEncryption(base_path)

# Manage all config files
results = cfg.enable_all()    # Encrypt all
results = cfg.disable_all()   # Decrypt all
status = cfg.get_status()     # Check status
```

### Encrypted File Manager

```python
from lib.security.encrypted_files import init_encryption, load_encrypted_json, save_encrypted_json

# Initialize (done in app.py automatically)
init_encryption(base_path)

# Use helper functions
data = load_encrypted_json("path/file.json")
save_encrypted_json("path/file.json", data)
```

---

## Integration Examples

### Using in Custom Code

```python
from lib.security.encrypted_files import load_encrypted_json, save_encrypted_json

# Load encrypted file
config = load_encrypted_json("data/my_config.json")

# Modify
config["new_key"] = "new_value"

# Save (auto-encrypted if enabled)
save_encrypted_json("data/my_config.json", config)
```

### Custom File Manager

```python
from lib.security import EncryptionManager

class CustomManager:
    def __init__(self, base_path):
        self.encryption = EncryptionManager(base_path)
    
    def load_data(self, path):
        return self.encryption.load_json_file(path)
    
    def save_data(self, path, data):
        self.encryption.save_json_file(path, data)
```

---

## FAQ

**Q: Do I need to enable encryption?**
A: Yes, for production security. It's automatic but you should backup the key.

**Q: What if I lose the encryption key?**
A: You cannot decrypt files. Always backup the key using `encrypt_config.py backup`.

**Q: Can I change the encryption key?**
A: Yes, via key rotation process documented above.

**Q: Does encryption slow down the app?**
A: Negligible impact (~1-5ms per operation).

**Q: Can I partially encrypt files?**
A: Currently no, but easy to extend (see Advanced Configuration).

**Q: What's the encryption algorithm?**
A: AES-128 in CBC mode with HMAC authentication (Fernet).

**Q: Is the key stored securely?**
A: Yes, with restricted permissions (0600). You should still backup separately.

---

## Support & Documentation

For more information:
- [SECURITY.md](SECURITY.md) - Overall security guide
- [SECURITY_SETUP.md](SECURITY_SETUP.md) - Quick setup guide
- `lib/security/encryption.py` - Implementation details
- `encrypt_config.py` - CLI tool usage

---

**Last Updated:** April 25, 2026  
**Encryption Version:** 1.0
