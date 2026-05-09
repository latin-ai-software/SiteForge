# lib/modmail_crypto.py

import os
import hashlib
import hmac
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.exceptions import InvalidKey

class ModmailCrypto:
    """End-to-end encryption for modmail using password-derived keys"""

    # PBKDF2 parameters
    SALT_LENGTH = 32
    KEY_LENGTH = 32  # 256-bit key
    ITERATIONS = 100000

    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
        """Derive encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(ModmailCrypto.SALT_LENGTH)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=ModmailCrypto.KEY_LENGTH,
            salt=salt,
            iterations=ModmailCrypto.ITERATIONS,
            backend=default_backend()
        )

        key = kdf.derive(password.encode('utf-8'))
        return key, salt

    @staticmethod
    def encrypt_message(message: str, password: str) -> dict:
        """Encrypt a message using password-derived key"""
        # Use a fixed salt for simplicity - in production, you'd want unique salts
        # but this ensures the same password always decrypts the same way
        salt = hashlib.sha256(password.encode('utf-8')).digest()[:16]

        key, _ = ModmailCrypto.derive_key(password, salt)

        # Generate random IV
        iv = os.urandom(16)

        # Pad the message
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(message.encode('utf-8')) + padder.finalize()

        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }

    @staticmethod
    def decrypt_message(encrypted_data: dict, password: str) -> str:
        """Decrypt a message using password-derived key"""
        try:
            # Decode base64
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            iv = base64.b64decode(encrypted_data['iv'])
            salt = base64.b64decode(encrypted_data['salt'])

            # Derive key
            key, _ = ModmailCrypto.derive_key(password, salt)

            # Decrypt
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()

            # Unpad
            unpadder = padding.PKCS7(128).unpadder()
            data = unpadder.update(padded_data) + unpadder.finalize()

            return data.decode('utf-8')

        except (ValueError, InvalidKey, KeyError) as e:
            raise ValueError("Failed to decrypt message - invalid password or corrupted data")

    @staticmethod
    def generate_message_hash(content: str, timestamp: str) -> str:
        """Generate a hash of the message for integrity verification"""
        message_data = f"{content}|{timestamp}"
        return hashlib.sha256(message_data.encode('utf-8')).hexdigest()

    @staticmethod
    def verify_message_integrity(content: str, timestamp: str, expected_hash: str) -> bool:
        """Verify message integrity using hash"""
        calculated_hash = ModmailCrypto.generate_message_hash(content, timestamp)
        return hmac.compare_digest(calculated_hash, expected_hash)