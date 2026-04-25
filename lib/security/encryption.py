"""
File encryption and decryption module for securing configuration files
Uses Fernet (symmetric encryption) from cryptography library
"""

import os
import json
from cryptography.fernet import Fernet, InvalidToken
from pathlib import Path


class EncryptionManager:
    """Handles encryption/decryption of JSON configuration files"""
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.key_file = os.path.join(base_path, "data", ".encryption_key")
        self.enabled_flag_file = os.path.join(base_path, "data", ".encryption_enabled")
        os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
        
        # Initialize encryption key if not exists
        self._ensure_key_exists()
    
    def _ensure_key_exists(self):
        """Create encryption key if it doesn't exist"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Restrict permissions on key file (Unix-like)
            try:
                os.chmod(self.key_file, 0o600)
            except:
                pass
    
    def _get_cipher(self):
        """Get Fernet cipher instance"""
        if not os.path.exists(self.key_file):
            self._ensure_key_exists()
        
        with open(self.key_file, 'rb') as f:
            key = f.read()
        
        try:
            return Fernet(key)
        except Exception as e:
            raise RuntimeError(f"Invalid encryption key: {e}")
    
    def is_enabled(self):
        """Check if encryption is enabled"""
        return os.path.exists(self.enabled_flag_file)
    
    def enable_encryption(self):
        """Enable encryption globally"""
        with open(self.enabled_flag_file, 'w') as f:
            f.write('enabled')
    
    def disable_encryption(self):
        """Disable encryption globally"""
        if os.path.exists(self.enabled_flag_file):
            os.remove(self.enabled_flag_file)
    
    def encrypt_data(self, data):
        """
        Encrypt data (dict or string)
        Returns bytes
        """
        if isinstance(data, dict):
            data = json.dumps(data, indent=4, default=str)
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data)
        return encrypted
    
    def decrypt_data(self, encrypted_data):
        """
        Decrypt data
        Returns bytes (still need to decode/json.load)
        """
        if isinstance(encrypted_data, str):
            encrypted_data = encrypted_data.encode('utf-8')
        
        cipher = self._get_cipher()
        try:
            decrypted = cipher.decrypt(encrypted_data)
            return decrypted
        except InvalidToken:
            raise ValueError("Failed to decrypt data - invalid encryption key or corrupted data")
    
    def encrypt_file(self, filepath):
        """
        Encrypt a file in place
        Reads plaintext, writes encrypted version
        """
        if not os.path.exists(filepath):
            return False, "File not found"
        
        try:
            with open(filepath, 'rb') as f:
                plaintext = f.read()
            
            encrypted = self.encrypt_data(plaintext)
            
            with open(filepath, 'wb') as f:
                f.write(encrypted)
            
            return True, "File encrypted"
        except Exception as e:
            return False, str(e)
    
    def decrypt_file(self, filepath):
        """
        Decrypt a file in place
        Reads encrypted, writes plaintext
        """
        if not os.path.exists(filepath):
            return False, "File not found"
        
        try:
            with open(filepath, 'rb') as f:
                encrypted = f.read()
            
            decrypted = self.decrypt_data(encrypted)
            
            with open(filepath, 'wb') as f:
                f.write(decrypted)
            
            return True, "File decrypted"
        except Exception as e:
            return False, str(e)
    
    def is_file_encrypted(self, filepath):
        """Check if a file is encrypted (heuristic)"""
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'rb') as f:
                header = f.read(10)
            
            # Fernet format starts with 'gAAAAA' in base64
            # Encrypted files are binary, not valid UTF-8 or JSON
            # Try to parse as JSON - if fails, likely encrypted
            f.seek(0)
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            return False  # Valid JSON = not encrypted
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Not valid JSON/UTF-8, likely encrypted or binary
            return True
        except:
            return False
    
    def load_json_file(self, filepath, auto_decrypt=True):
        """
        Load JSON file, decrypting if necessary
        Returns dict
        """
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Check if encrypted and decryption is enabled
            if self.is_file_encrypted(filepath) and auto_decrypt and self.is_enabled():
                data = self.decrypt_data(data)
            
            # Parse JSON
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            
            return json.loads(data)
        except Exception as e:
            raise RuntimeError(f"Failed to load {filepath}: {e}")
    
    def save_json_file(self, filepath, data, auto_encrypt=True):
        """
        Save JSON file, encrypting if enabled
        """
        try:
            json_str = json.dumps(data, indent=4, default=str)
            json_bytes = json_str.encode('utf-8')
            
            # Encrypt if enabled
            if auto_encrypt and self.is_enabled():
                json_bytes = self.encrypt_data(json_bytes)
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(json_bytes)
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to save {filepath}: {e}")


class ConfigEncryption:
    """High-level interface for managing encrypted configuration"""
    
    def __init__(self, base_path):
        self.encryption = EncryptionManager(base_path)
        self.base_path = base_path
        self.config_files = [
            os.path.join(base_path, "data", "settings.json"),
            os.path.join(base_path, "data", "users.json"),
            os.path.join(base_path, "data", "analytics.json"),
            os.path.join(base_path, "data", "comments.json"),
            os.path.join(base_path, "data", "posts_metadata.json"),
        ]
    
    def enable_all(self):
        """Enable encryption and encrypt all config files"""
        self.encryption.enable_encryption()
        
        results = {}
        for filepath in self.config_files:
            if os.path.exists(filepath):
                try:
                    # Only encrypt if not already encrypted
                    if not self.encryption.is_file_encrypted(filepath):
                        success, msg = self.encryption.encrypt_file(filepath)
                        results[filepath] = (success, msg)
                except Exception as e:
                    results[filepath] = (False, str(e))
        
        return results
    
    def disable_all(self):
        """Decrypt all config files and disable encryption"""
        results = {}
        for filepath in self.config_files:
            if os.path.exists(filepath):
                try:
                    # Only decrypt if encrypted
                    if self.encryption.is_file_encrypted(filepath):
                        success, msg = self.encryption.decrypt_file(filepath)
                        results[filepath] = (success, msg)
                except Exception as e:
                    results[filepath] = (False, str(e))
        
        self.encryption.disable_encryption()
        return results
    
    def get_status(self):
        """Get encryption status of all config files"""
        status = {
            "encryption_enabled": self.encryption.is_enabled(),
            "files": {}
        }
        
        for filepath in self.config_files:
            if os.path.exists(filepath):
                is_encrypted = self.encryption.is_file_encrypted(filepath)
                status["files"][filepath] = {
                    "exists": True,
                    "encrypted": is_encrypted,
                    "size": os.path.getsize(filepath)
                }
            else:
                status["files"][filepath] = {
                    "exists": False,
                    "encrypted": False,
                    "size": 0
                }
        
        return status
