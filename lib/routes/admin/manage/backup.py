import os
import zipfile
import datetime
import json
from flask import Blueprint, send_file, render_template, redirect, url_for, flash, request, jsonify, current_app
from .remote_backup import RemoteBackupHandler

backup_bp = Blueprint('backup', __name__, url_prefix='/admin/manage/backup')

# Basisverzeichnis des Projekts (absolute Pfade!)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

# Ordner, die gesichert werden sollen
BACKUP_TARGETS = [
    os.path.join(BASE_DIR, "data/posts"),
    os.path.join(BASE_DIR, "data/uploads"),
    os.path.join(BASE_DIR, "plugins")
]

# Backup-Speicherort
BACKUP_DIR = os.path.join(BASE_DIR, "updater/backups")


# Sicherstellen, dass der Backup-Ordner existiert
def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


# Backup erstellen
def create_backup_file():
    ensure_backup_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.zip"
    filepath = os.path.join(BACKUP_DIR, filename)

    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        for target in BACKUP_TARGETS:
            if os.path.exists(target):
                for root, dirs, files in os.walk(target):
                    for file in files:
                        full_path = os.path.join(root, file)

                        # relativer Pfad im ZIP (schön & sauber)
                        arcname = os.path.relpath(full_path, start=BASE_DIR)

                        zf.write(full_path, arcname)

    return filename, filepath


# Backups auflisten
def list_backups():
    ensure_backup_dir()
    files = []
    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if name.endswith(".zip"):
            path = os.path.join(BACKUP_DIR, name)
            size = os.path.getsize(path)
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            files.append({
                "name": name,
                "size": size,
                "mtime": mtime,
            })
    return files


# Älteste Backups löschen, wenn mehr als 10 existieren
def cleanup_old_backups(limit=10):
    ensure_backup_dir()
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")],
        key=lambda x: os.path.getmtime(os.path.join(BACKUP_DIR, x)),
        reverse=True
    )

    if len(files) > limit:
        for old in files[limit:]:
            os.remove(os.path.join(BACKUP_DIR, old))


# Admin-Panel: Backup-Liste
@backup_bp.route("/")
def backup_index():
    backups = list_backups()
    return render_template("admin/backup/index.html", backups=backups)


# Neues Backup erstellen
@backup_bp.route("/create")
def backup_create():
    filename, _ = create_backup_file()
    cleanup_old_backups(limit=10)
    flash(f"Backup erstellt: {filename}", "success")
    return redirect(url_for("backup.backup_index"))


# Backup herunterladen
@backup_bp.route("/download/<name>")
def backup_download(name):
    ensure_backup_dir()
    path = os.path.join(BACKUP_DIR, name)
    if not os.path.exists(path):
        flash("Backup nicht gefunden.", "error")
        return redirect(url_for("backup.backup_index"))

    return send_file(
        path,
        mimetype="application/zip",
        as_attachment=True,
        download_name=name
    )


# Backup löschen
@backup_bp.route("/delete/<name>")
def backup_delete(name):
    ensure_backup_dir()
    path = os.path.join(BACKUP_DIR, name)
    if os.path.exists(path):
        os.remove(path)
        flash(f"Backup gelöscht: {name}", "success")
    else:
        flash("Backup nicht gefunden.", "error")

    return redirect(url_for("backup.backup_index"))


# Remote Backup Settings
@backup_bp.route("/remote-settings", methods=["GET", "POST"])
def remote_settings():
    """Manage remote backup settings"""
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    
    if request.method == "POST":
        # Load existing settings
        settings = {}
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        
        # Update remote backup settings
        settings['backup_scp_enabled'] = request.form.get('scp_enabled') == 'on'
        settings['backup_scp_host'] = request.form.get('scp_host', '')
        settings['backup_scp_port'] = int(request.form.get('scp_port', 22))
        settings['backup_scp_user'] = request.form.get('scp_user', '')
        settings['backup_scp_password'] = request.form.get('scp_password', '')
        settings['backup_scp_remote_path'] = request.form.get('scp_remote_path', '/backups/')
        
        settings['backup_ftp_enabled'] = request.form.get('ftp_enabled') == 'on'
        settings['backup_ftp_host'] = request.form.get('ftp_host', '')
        settings['backup_ftp_port'] = int(request.form.get('ftp_port', 21))
        settings['backup_ftp_user'] = request.form.get('ftp_user', '')
        settings['backup_ftp_password'] = request.form.get('ftp_password', '')
        settings['backup_ftp_remote_path'] = request.form.get('ftp_remote_path', '/backups/')
        
        settings['backup_https_enabled'] = request.form.get('https_enabled') == 'on'
        settings['backup_https_url'] = request.form.get('https_url', '')
        settings['backup_https_token'] = request.form.get('https_token', '')
        
        # Save settings
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        flash("Einstellungen für Remote-Backup gespeichert.", "success")
        return redirect(url_for("backup.remote_settings"))
    
    # Load current settings
    settings = {}
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    
    from flask import get_flashed_messages
    messages = get_flashed_messages(with_categories=True)
    
    return render_template("admin/backup/remote_settings.html", settings=settings, messages=messages)


# API: Test remote connection
@backup_bp.route("/api/test-remote", methods=["POST"])
def test_remote():
    """Test remote backup connection"""
    protocol = request.json.get('protocol', '')
    
    if protocol == 'scp':
        try:
            import paramiko
        except ImportError:
            return jsonify({
                'success': False,
                'message': 'paramiko not installed'
            }), 500
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                request.json.get('host'),
                port=int(request.json.get('port', 22)),
                username=request.json.get('user'),
                password=request.json.get('password'),
                timeout=5
            )
            ssh.close()
            return jsonify({'success': True, 'message': 'Connection successful'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    elif protocol == 'ftp':
        try:
            from ftplib import FTP
            ftp = FTP()
            ftp.connect(request.json.get('host'), port=int(request.json.get('port', 21)), timeout=5)
            ftp.login(request.json.get('user'), request.json.get('password'))
            ftp.quit()
            return jsonify({'success': True, 'message': 'Connection successful'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    elif protocol == 'https':
        try:
            import requests
            headers = {}
            if request.json.get('token'):
                headers['Authorization'] = f"Bearer {request.json.get('token')}"
            
            response = requests.head(request.json.get('url'), headers=headers, timeout=5)
            if response.status_code < 400:
                return jsonify({'success': True, 'message': 'Connection successful'})
            else:
                return jsonify({'success': False, 'message': f'HTTP {response.status_code}'}), 400
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return jsonify({'success': False, 'message': 'Unknown protocol'}), 400


# API: Get remote destinations
@backup_bp.route("/api/destinations")
def get_destinations():
    """Get configured remote backup destinations"""
    handler = RemoteBackupHandler(current_app.root_path)
    destinations = handler.get_configured_destinations()
    return jsonify({'destinations': destinations})


# API: Upload backup to remote
@backup_bp.route("/api/upload-remote/<backup_name>", methods=["POST"])
def upload_remote_backup(backup_name):
    """Upload specific backup to remote servers"""
    ensure_backup_dir()
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if not os.path.exists(backup_path):
        return jsonify({'success': False, 'message': 'Backup not found'}), 404
    
    handler = RemoteBackupHandler(current_app.root_path)
    results = handler.upload_backup(backup_path)
    
    return jsonify({
        'success': True,
        'results': results
    })
