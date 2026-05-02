#!/usr/bin/env python3
"""
Encryption system verification and testing script
"""

import os
import sys
import json
import tempfile
from pathlib import Path


def test_encryption():
    """Test the encryption system"""
    print("\n" + "="*60)
    print("ENCRYPTION SYSTEM VERIFICATION")
    print("="*60 + "\n")
    
    # Get base path
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)
    
    # Test 1: Import modules
    print("Test 1: Importing encryption modules...")
    try:
        from lib.security import EncryptionManager, ConfigEncryption
        from lib.security.encrypted_files import init_encryption, get_encryption_manager
        from cryptography.fernet import Fernet
        print("  ✓ All modules imported successfully\n")
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        print("  Install cryptography: pip install cryptography")
        return False
    
    # Test 2: Create temporary test environment
    print("Test 2: Creating temporary test environment...")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_data_dir = os.path.join(tmpdir, "data")
        os.makedirs(test_data_dir)
        
        try:
            # Initialize encryption manager
            enc_mgr = EncryptionManager(tmpdir)
            print("  ✓ Encryption manager initialized")
            
            # Test 3: Generate and verify key
            print("\nTest 3: Verifying encryption key...")
            key_file = os.path.join(test_data_dir, ".encryption_key")
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    key = f.read()
                try:
                    Fernet(key)
                    print(f"  ✓ Valid Fernet key generated ({len(key)} bytes)")
                except:
                    print("  ✗ Invalid key format")
                    return False
            else:
                print("  ✗ Key file not created")
                return False
            
            # Test 4: Encrypt/decrypt data
            print("\nTest 4: Testing encryption/decryption...")
            test_data = {"username": "admin", "secret": "password123"}
            
            encrypted = enc_mgr.encrypt_data(test_data)
            print(f"  ✓ Data encrypted ({len(encrypted)} bytes)")
            
            decrypted = enc_mgr.decrypt_data(encrypted)
            decrypted_data = json.loads(decrypted.decode('utf-8'))
            
            if decrypted_data == test_data:
                print("  ✓ Data decrypted successfully and matches original")
            else:
                print("  ✗ Decrypted data doesn't match")
                return False
            
            # Test 5: File encryption/decryption
            print("\nTest 5: Testing file operations...")
            test_file = os.path.join(test_data_dir, "test.json")
            
            # Write unencrypted file
            with open(test_file, 'w') as f:
                json.dump(test_data, f)
            
            original_size = os.path.getsize(test_file)
            
            # Encrypt file
            success, msg = enc_mgr.encrypt_file(test_file)
            if success:
                print(f"  ✓ File encrypted: {msg}")
            else:
                print(f"  ✗ File encryption failed: {msg}")
                return False
            
            encrypted_size = os.path.getsize(test_file)
            print(f"    Original: {original_size} bytes → Encrypted: {encrypted_size} bytes")
            
            # Verify encrypted file is not readable as JSON
            try:
                with open(test_file, 'r') as f:
                    json.load(f)
                print("  ✗ Encrypted file still readable as JSON (not encrypted properly)")
                return False
            except:
                print("  ✓ Encrypted file is not readable as plain JSON")
            
            # Decrypt file
            success, msg = enc_mgr.decrypt_file(test_file)
            if success:
                print(f"  ✓ File decrypted: {msg}")
            else:
                print(f"  ✗ File decryption failed: {msg}")
                return False
            
            # Verify decrypted content
            with open(test_file, 'r') as f:
                decrypted_file_data = json.load(f)
            
            if decrypted_file_data == test_data:
                print("  ✓ Decrypted file content matches original")
            else:
                print("  ✗ Decrypted file content doesn't match")
                return False
            
            # Test 6: ConfigEncryption
            print("\nTest 6: Testing ConfigEncryption wrapper...")
            cfg_enc = ConfigEncryption(tmpdir)
            status = cfg_enc.get_status()
            
            print(f"  ✓ Encryption enabled: {status['encryption_enabled']}")
            print(f"  ✓ Status retrieved for {len(status['files'])} files")
            
            # Test 7: Enable/disable
            print("\nTest 7: Testing enable/disable...")
            enc_mgr.enable_encryption()
            if enc_mgr.is_enabled():
                print("  ✓ Encryption enabled successfully")
            else:
                print("  ✗ Failed to enable encryption")
                return False
            
            enc_mgr.disable_encryption()
            if not enc_mgr.is_enabled():
                print("  ✓ Encryption disabled successfully")
            else:
                print("  ✗ Failed to disable encryption")
                return False
            
        except Exception as e:
            print(f"  ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Test 8: Check if cryptography is installed
    print("\nTest 8: Checking system configuration...")
    try:
        import cryptography
        print(f"  ✓ cryptography library installed (version {cryptography.__version__})")
    except ImportError:
        print("  ✗ cryptography library not installed")
        print("    Install with: pip install cryptography")
        return False
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED - Encryption system is working!")
    print("="*60 + "\n")
    
    return True


def show_current_status():
    """Show current encryption status of actual data files"""
    print("\n" + "="*60)
    print("CURRENT ENCRYPTION STATUS")
    print("="*60 + "\n")
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)
    
    try:
        from lib.security import ConfigEncryption
        
        cfg_enc = ConfigEncryption(base_path)
        status = cfg_enc.get_status()
        
        print(f"Encryption System: {'ENABLED ✓' if status['encryption_enabled'] else 'DISABLED ✗'}")
        print(f"\nConfiguration Files:")
        print("-" * 60)
        
        for filepath, file_status in status["files"].items():
            filename = os.path.basename(filepath)
            if file_status["exists"]:
                encrypted = "🔒 ENCRYPTED" if file_status["encrypted"] else "🔓 PLAIN"
                size = file_status["size"]
                print(f"  {filename:<30} {encrypted:<15} {size:>10} bytes")
            else:
                print(f"  {filename:<30} {'(not yet created)':<15}")
        
        print("-" * 60)
        
        encryption_key = os.path.join(base_path, "data", ".encryption_key")
        if os.path.exists(encryption_key):
            size = os.path.getsize(encryption_key)
            print(f"\nEncryption Key: Present ({size} bytes)")
            print(f"Key Location: {encryption_key}")
        else:
            print("\nEncryption Key: Not found")
        
        print()
    
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test encryption system")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["test", "status"],
        default="test",
        help="Command to run"
    )
    
    args = parser.parse_args()
    
    if args.command == "test":
        success = test_encryption()
        sys.exit(0 if success else 1)
    elif args.command == "status":
        success = show_current_status()
        sys.exit(0 if success else 1)
