"""
Transparent encryption wrapper for file operations
Automatically encrypts/decrypts files based on encryption settings
"""

import os
import json
from .encryption import EncryptionManager


class EncryptedFileManager:
    """
    Transparent wrapper for file operations
    Automatically handles encryption/decryption
    """
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.encryption = EncryptionManager(base_path)
    
    def load_json(self, filepath):
        """
        Load JSON file (automatically decrypts if encrypted)
        """
        return self.encryption.load_json_file(filepath, auto_decrypt=True)
    
    def save_json(self, filepath, data):
        """
        Save JSON file (automatically encrypts if enabled)
        """
        self.encryption.save_json_file(filepath, data, auto_encrypt=True)
    
    def load_json_raw(self, filepath):
        """
        Load JSON file without decryption (for admin purposes)
        """
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return json.loads(data)
        except:
            return None


# Global instance - will be initialized in app.py
_encryption_manager = None


def init_encryption(base_path):
    """Initialize encryption manager (call from app.py)"""
    global _encryption_manager
    _encryption_manager = EncryptedFileManager(base_path)
    return _encryption_manager


def get_encryption_manager():
    """Get global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        raise RuntimeError("Encryption manager not initialized. Call init_encryption() first.")
    return _encryption_manager


def load_encrypted_json(filepath):
    """Load JSON file with automatic decryption"""
    return get_encryption_manager().load_json(filepath)


def save_encrypted_json(filepath, data):
    """Save JSON file with automatic encryption"""
    return get_encryption_manager().save_json(filepath, data)
