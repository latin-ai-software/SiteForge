#!/usr/bin/env python3
"""
Configuration file encryption migration and management script
Usage:
  python encrypt_config.py enable      - Enable encryption
  python encrypt_config.py disable     - Disable encryption (decrypt)
  python encrypt_config.py status      - Show encryption status
  python encrypt_config.py backup      - Backup encryption key
  python encrypt_config.py restore KEY - Restore encryption key
"""

import os
import sys
import argparse
import shutil
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Manage configuration file encryption"
    )
    parser.add_argument(
        "command",
        choices=["enable", "disable", "status", "backup", "restore"],
        help="Command to execute"
    )
    parser.add_argument(
        "key",
        nargs="?",
        help="Encryption key (for restore command)"
    )
    
    args = parser.parse_args()
    
    # Get base path
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Import after determining base path
    sys.path.insert(0, base_path)
    from lib.security import ConfigEncryption
    
    config_enc = ConfigEncryption(base_path)
    
    if args.command == "status":
        status = config_enc.get_status()
        print("\n" + "="*60)
        print("ENCRYPTION STATUS")
        print("="*60)
        print(f"Encryption Enabled: {status['encryption_enabled']}")
        print(f"\nConfiguration Files:")
        print("-" * 60)
        
        for filepath, file_status in status["files"].items():
            filename = os.path.basename(filepath)
            if file_status["exists"]:
                encrypted = "🔒 ENCRYPTED" if file_status["encrypted"] else "🔓 PLAIN"
                size = file_status["size"]
                print(f"  {filename:<30} {encrypted:<15} {size:>10} bytes")
            else:
                print(f"  {filename:<30} {'NOT FOUND':<15}")
        
        print("-" * 60)
        print()
    
    elif args.command == "enable":
        print("\n" + "="*60)
        print("ENABLING ENCRYPTION")
        print("="*60)
        
        status = config_enc.get_status()
        if status["encryption_enabled"]:
            print("✓ Encryption is already enabled!")
        else:
            print("Starting encryption of configuration files...")
            results = config_enc.enable_all()
            
            success_count = 0
            for filepath, (success, msg) in results.items():
                filename = os.path.basename(filepath)
                if success:
                    print(f"  ✓ {filename}: {msg}")
                    success_count += 1
                else:
                    print(f"  ✗ {filename}: {msg}")
            
            print(f"\n✓ Successfully encrypted {success_count} files")
            print("\n⚠️  IMPORTANT: Backup your encryption key!")
            print("   Location: data/.encryption_key")
            print("   Run: python encrypt_config.py backup")
        
        print()
    
    elif args.command == "disable":
        print("\n" + "="*60)
        print("DISABLING ENCRYPTION (DANGEROUS)")
        print("="*60)
        print("\n⚠️  WARNING: This will decrypt all configuration files!")
        print("    Configuration files will be readable as plain text.")
        print("\nAre you sure? Type 'yes' to continue: ", end="", flush=True)
        
        confirm = input().strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return
        
        print("\nDisabling encryption...")
        results = config_enc.disable_all()
        
        success_count = 0
        for filepath, (success, msg) in results.items():
            filename = os.path.basename(filepath)
            if success:
                print(f"  ✓ {filename}: {msg}")
                success_count += 1
            else:
                print(f"  ✗ {filename}: {msg}")
        
        print(f"\n✓ Successfully decrypted {success_count} files")
        print()
    
    elif args.command == "backup":
        print("\n" + "="*60)
        print("BACKING UP ENCRYPTION KEY")
        print("="*60)
        
        key_file = os.path.join(base_path, "data", ".encryption_key")
        
        if not os.path.exists(key_file):
            print("✗ Encryption key not found at:", key_file)
            return
        
        # Create backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(
            base_path,
            "data",
            f".encryption_key.backup_{timestamp}"
        )
        
        try:
            shutil.copy2(key_file, backup_file)
            
            # Read and display key info
            with open(key_file, 'rb') as f:
                key_data = f.read()
            
            print(f"✓ Key backed up to: {backup_file}")
            print(f"  Key size: {len(key_data)} bytes")
            print(f"  Backup file size: {os.path.getsize(backup_file)} bytes")
            
            # Print key in base64 for manual backup
            import base64
            key_b64 = base64.b64encode(key_data).decode('utf-8')
            print(f"\n📋 SAVE THIS BACKUP SAFELY:")
            print("-" * 60)
            print(key_b64)
            print("-" * 60)
            print("\nStore this backup in a secure location!")
            
        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return
        
        print()
    
    elif args.command == "restore":
        if not args.key:
            print("✗ Restoration key required. Usage: python encrypt_config.py restore <key>")
            return
        
        print("\n" + "="*60)
        print("RESTORING ENCRYPTION KEY")
        print("="*60)
        print("\n⚠️  WARNING: This will overwrite the current encryption key!")
        print("    Files encrypted with the old key will become unreadable.")
        print("\nAre you sure? Type 'yes' to continue: ", end="", flush=True)
        
        confirm = input().strip().lower()
        if confirm != "yes":
            print("Cancelled.")
            return
        
        try:
            import base64
            
            # Decode the provided key
            key_data = base64.b64decode(args.key)
            
            # Verify it's a valid Fernet key
            from cryptography.fernet import Fernet
            try:
                Fernet(key_data)
            except:
                print("✗ Invalid encryption key format")
                return
            
            # Backup current key first
            key_file = os.path.join(base_path, "data", ".encryption_key")
            if os.path.exists(key_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(
                    base_path,
                    "data",
                    f".encryption_key.backup_{timestamp}"
                )
                shutil.copy2(key_file, backup_file)
                print(f"✓ Current key backed up to: {backup_file}")
            
            # Restore new key
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key_data)
            
            try:
                os.chmod(key_file, 0o600)
            except OSError as e:
                print(f"Warning: Could not set file permissions: {e}")
            
            print("✓ Encryption key restored successfully")
            
        except Exception as e:
            print(f"✗ Restoration failed: {e}")
            return
        
        print()


if __name__ == "__main__":
    main()
