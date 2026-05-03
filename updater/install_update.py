#!/usr/bin/env python3
"""
Standalone update installation script
Runs as a background process independent of the Flask application
This allows the app to restart while the update is being installed
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
import requests
import logging
from pathlib import Path
from datetime import datetime

# Setup logging for background process
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'update_install_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def install_update(base_path, license_key, version):
    """
    Download and install update from remote server
    
    Args:
        base_path: Root directory of the application
        license_key: License key for authentication
        version: Current version string
    """
    try:
        logger.info(f"Starting update installation for version {version}")
        logger.info(f"Base path: {base_path}")
        
        # Validate base path
        if not os.path.exists(base_path):
            logger.error(f"Base path does not exist: {base_path}")
            return False
        
        # Build update URL
        update_url = f"https://latinai.ch/wp-json/shoplicensegateway/updater/SF/update?version={version}&license_key={license_key}"
        logger.info(f"Update URL: {update_url}")
        
        # Download update
        logger.info("Downloading update package...")
        try:
            response = requests.get(update_url, timeout=300)  # 5 minute timeout
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download update: {str(e)}")
            return False
        
        logger.info(f"Downloaded {len(response.content)} bytes")
        
        # Extract and install
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Save ZIP file
            logger.info("Saving ZIP file...")
            try:
                with open(zip_path, "wb") as f:
                    f.write(response.content)
            except Exception as e:
                logger.error(f"Failed to save ZIP file: {str(e)}")
                return False
            
            # Extract ZIP file
            logger.info("Extracting update package...")
            extract_path = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
            except zipfile.BadZipFile as e:
                logger.error(f"Invalid ZIP file: {str(e)}")
                return False
            except Exception as e:
                logger.error(f"Failed to extract ZIP: {str(e)}")
                return False
            
            # Get list of files
            extracted_files = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), extract_path)
                    extracted_files.append(rel_path)
            
            logger.info(f"Found {len(extracted_files)} files to install")
            
            # Create backup before installation
            backup_dir = os.path.join(
                base_path, 
                'updater', 
                'backups', 
                f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            )
            os.makedirs(backup_dir, exist_ok=True)
            logger.info(f"Creating backup at {backup_dir}")
            
            # Copy files to installation directory
            logger.info("Installing files...")
            updated_files = []
            failed_files = []
            
            for rel_path in extracted_files:
                try:
                    source_path = os.path.join(extract_path, rel_path)
                    target_path = os.path.join(base_path, rel_path)
                    
                    # Create target directory if it doesn't exist
                    target_dir = os.path.dirname(target_path)
                    os.makedirs(target_dir, exist_ok=True)
                    
                    # Create backup of existing file
                    if os.path.exists(target_path):
                        backup_path = os.path.join(backup_dir, rel_path)
                        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                        shutil.copy2(target_path, backup_path)
                        logger.debug(f"Backed up {rel_path}")
                    
                    # Copy new file
                    shutil.copy2(source_path, target_path)
                    updated_files.append(rel_path)
                    logger.debug(f"Installed {rel_path}")
                    
                except Exception as e:
                    logger.error(f"Failed to install {rel_path}: {str(e)}")
                    failed_files.append(rel_path)
            
            # Log installation results
            logger.info(f"Successfully installed {len(updated_files)} files")
            if failed_files:
                logger.warning(f"Failed to install {len(failed_files)} files: {failed_files}")
            
            # Update version file
            version_file = os.path.join(base_path, "data", "version.json")
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    version_data = json.load(f)
                
                # Update to new version
                version_data["current_version"] = version_data.get("latest_version", version)
                version_data["requires_update"] = False
                version_data["last_update"] = datetime.now().isoformat()
                
                with open(version_file, "w", encoding="utf-8") as f:
                    json.dump(version_data, f, indent=4)
                
                logger.info("Updated version.json")
            except Exception as e:
                logger.error(f"Failed to update version.json: {str(e)}")
            
            # Write installation log
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "version": version,
                "files_installed": len(updated_files),
                "files_failed": len(failed_files),
                "backup_location": backup_dir,
                "status": "success" if not failed_files else "partial"
            }
            
            log_file_path = os.path.join(base_path, "data", "update_log.json")
            try:
                logs = []
                if os.path.exists(log_file_path):
                    with open(log_file_path, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                
                logs.append(log_entry)
                with open(log_file_path, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=4)
            except Exception as e:
                logger.error(f"Failed to write update log: {str(e)}")
            
            logger.info("Update installation completed successfully!")
            return True
    
    except Exception as e:
        logger.error(f"Unexpected error during update: {str(e)}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python install_update.py <base_path> <license_key> <version>")
        sys.exit(1)
    
    base_path = sys.argv[1]
    license_key = sys.argv[2]
    version = sys.argv[3]
    
    success = install_update(base_path, license_key, version)
    sys.exit(0 if success else 1)
