#!/usr/bin/env python3
"""
Automatic Backup Script - Creates and optionally uploads backups to remote servers
"""
import os
import sys
import json
from datetime import datetime
from lib.routes.admin.manage.backup import create_backup_file, cleanup_old_backups
from lib.routes.admin.manage.remote_backup import RemoteBackupHandler

# Get base path
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

def log(message: str):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_backup(upload_remote: bool = True, verbose: bool = False):
    """
    Run automatic backup and optionally upload to remote servers
    
    Args:
        upload_remote: Whether to upload to configured remote servers
        verbose: Whether to print detailed output
    """
    try:
        log("Starting automatic backup...")
        
        # Create backup
        filename, filepath = create_backup_file()
        log(f"Backup created: {filename}")
        log(f"Backup size: {os.path.getsize(filepath) / (1024*1024):.2f} MB")
        
        # Cleanup old backups
        cleanup_old_backups(limit=10)
        log("Old backups cleaned up (keeping 10 most recent)")
        
        # Upload to remote servers if configured
        if upload_remote:
            remote_handler = RemoteBackupHandler(BASE_PATH)
            destinations = remote_handler.get_configured_destinations()
            
            if destinations:
                log(f"Uploading to {len(destinations)} remote destination(s)...")
                results = remote_handler.upload_backup(filepath)
                
                for protocol, uploads in results.items():
                    for host, success, message in uploads:
                        if verbose:
                            status = "✓" if success else "✗"
                            log(f"  [{status}] {protocol.upper()} ({host}): {message}")
            else:
                if verbose:
                    log("No remote destinations configured")
        
        log("Automatic backup completed successfully")
        return True
        
    except Exception as e:
        log(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automatic backup script")
    parser.add_argument("--no-remote", action="store_true", help="Skip remote uploads")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    success = run_backup(
        upload_remote=not args.no_remote,
        verbose=args.verbose
    )
    
    sys.exit(0 if success else 1)
