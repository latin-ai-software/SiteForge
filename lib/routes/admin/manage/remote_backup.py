"""
Remote Backup Module - Upload backups to remote servers via scp, ftp, or https
"""
import os
import json
import requests
from pathlib import Path
from typing import Dict, Tuple, List, Optional


class RemoteBackupHandler:
    """Handle uploading backups to remote servers"""

    def __init__(self, base_path: str):
        """Initialize remote backup handler
        
        Args:
            base_path: Root path of the application
        """
        self.base_path = base_path
        self.settings_file = os.path.join(base_path, "data", "settings.json")

    def load_remote_settings(self) -> Dict:
        """Load remote backup settings from settings.json
        
        Returns:
            Dictionary with remote backup configuration
        """
        if not os.path.exists(self.settings_file):
            return {}
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return {
                    'scp_enabled': settings.get('backup_scp_enabled', False),
                    'scp_host': settings.get('backup_scp_host', ''),
                    'scp_port': settings.get('backup_scp_port', 22),
                    'scp_user': settings.get('backup_scp_user', ''),
                    'scp_password': settings.get('backup_scp_password', ''),
                    'scp_remote_path': settings.get('backup_scp_remote_path', '/backups/'),
                    'ftp_enabled': settings.get('backup_ftp_enabled', False),
                    'ftp_host': settings.get('backup_ftp_host', ''),
                    'ftp_port': settings.get('backup_ftp_port', 21),
                    'ftp_user': settings.get('backup_ftp_user', ''),
                    'ftp_password': settings.get('backup_ftp_password', ''),
                    'ftp_remote_path': settings.get('backup_ftp_remote_path', '/backups/'),
                    'https_enabled': settings.get('backup_https_enabled', False),
                    'https_url': settings.get('backup_https_url', ''),
                    'https_token': settings.get('backup_https_token', ''),
                }
        except Exception as e:
            return {}

    def upload_via_scp(self, local_path: str, remote_settings: Dict) -> Tuple[bool, str]:
        """Upload backup via SCP
        
        Args:
            local_path: Local path to backup file
            remote_settings: Remote SCP settings
        
        Returns:
            Tuple of (success, message)
        """
        if not remote_settings.get('scp_host'):
            return False, "SCP host not configured"
        
        try:
            import paramiko
        except ImportError:
            return False, "paramiko library not installed. Install with: pip install paramiko"

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                remote_settings['scp_host'],
                port=remote_settings.get('scp_port', 22),
                username=remote_settings['scp_user'],
                password=remote_settings['scp_password'],
                timeout=10
            )
            
            sftp = ssh.open_sftp()
            remote_path = remote_settings.get('scp_remote_path', '/backups/')
            
            # Create remote directory if it doesn't exist
            try:
                sftp.stat(remote_path)
            except IOError:
                sftp.mkdir(remote_path)
            
            filename = os.path.basename(local_path)
            remote_filepath = os.path.join(remote_path, filename).replace('\\', '/')
            
            sftp.put(local_path, remote_filepath)
            sftp.close()
            ssh.close()
            
            return True, f"Backup uploaded to {remote_settings['scp_host']}: {remote_filepath}"
        except Exception as e:
            return False, f"SCP upload failed: {str(e)}"

    def upload_via_ftp(self, local_path: str, remote_settings: Dict) -> Tuple[bool, str]:
        """Upload backup via FTP
        
        Args:
            local_path: Local path to backup file
            remote_settings: Remote FTP settings
        
        Returns:
            Tuple of (success, message)
        """
        try:
            from ftplib import FTP, error_perm, error_temp
        except ImportError:
            return False, "ftplib not available"

        if not remote_settings.get('ftp_host'):
            return False, "FTP host not configured"

        try:
            ftp = FTP()
            ftp.connect(
                remote_settings['ftp_host'],
                port=remote_settings.get('ftp_port', 21),
                timeout=10
            )
            ftp.login(remote_settings['ftp_user'], remote_settings['ftp_password'])
            
            remote_path = remote_settings.get('ftp_remote_path', '/backups/')
            
            # Try to change to remote directory, create if needed
            try:
                ftp.cwd(remote_path)
            except error_perm:
                ftp.mkd(remote_path)
                ftp.cwd(remote_path)
            
            filename = os.path.basename(local_path)
            
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            ftp.quit()
            
            return True, f"Backup uploaded to FTP {remote_settings['ftp_host']}: {filename}"
        except Exception as e:
            return False, f"FTP upload failed: {str(e)}"

    def upload_via_https(self, local_path: str, remote_settings: Dict) -> Tuple[bool, str]:
        """Upload backup via HTTPS
        
        Args:
            local_path: Local path to backup file
            remote_settings: Remote HTTPS settings
        
        Returns:
            Tuple of (success, message)
        """
        if not remote_settings.get('https_url'):
            return False, "HTTPS URL not configured"

        try:
            url = remote_settings['https_url']
            if not url.endswith('/'):
                url += '/'
            
            filename = os.path.basename(local_path)
            headers = {}
            
            if remote_settings.get('https_token'):
                headers['Authorization'] = f"Bearer {remote_settings['https_token']}"
            
            with open(local_path, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(
                    url,
                    files=files,
                    headers=headers,
                    timeout=30
                )
            
            if response.status_code in [200, 201]:
                return True, f"Backup uploaded to {url}: {filename}"
            else:
                return False, f"HTTPS upload failed: HTTP {response.status_code}"
        except Exception as e:
            return False, f"HTTPS upload failed: {str(e)}"

    def upload_backup(self, local_path: str) -> Dict[str, List[Tuple[str, bool, str]]]:
        """Upload backup to all configured remote destinations
        
        Args:
            local_path: Local path to backup file
        
        Returns:
            Dictionary with upload results for each protocol
        """
        results = {
            'scp': [],
            'ftp': [],
            'https': []
        }
        
        settings = self.load_remote_settings()
        
        if settings.get('scp_enabled'):
            success, message = self.upload_via_scp(local_path, settings)
            results['scp'].append((settings.get('scp_host', 'unknown'), success, message))
        
        if settings.get('ftp_enabled'):
            success, message = self.upload_via_ftp(local_path, settings)
            results['ftp'].append((settings.get('ftp_host', 'unknown'), success, message))
        
        if settings.get('https_enabled'):
            success, message = self.upload_via_https(local_path, settings)
            results['https'].append((settings.get('https_url', 'unknown'), success, message))
        
        return results

    def get_configured_destinations(self) -> List[Dict]:
        """Get list of configured remote backup destinations
        
        Returns:
            List of configured destination dictionaries
        """
        settings = self.load_remote_settings()
        destinations = []
        
        if settings.get('scp_enabled') and settings.get('scp_host'):
            destinations.append({
                'type': 'SCP',
                'host': settings['scp_host'],
                'port': settings.get('scp_port', 22),
                'path': settings.get('scp_remote_path', '/backups/')
            })
        
        if settings.get('ftp_enabled') and settings.get('ftp_host'):
            destinations.append({
                'type': 'FTP',
                'host': settings['ftp_host'],
                'port': settings.get('ftp_port', 21),
                'path': settings.get('ftp_remote_path', '/backups/')
            })
        
        if settings.get('https_enabled') and settings.get('https_url'):
            destinations.append({
                'type': 'HTTPS',
                'url': settings['https_url']
            })
        
        return destinations
