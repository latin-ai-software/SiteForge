import os
import zipfile
import datetime
from flask import Blueprint, send_file, render_template, redirect, url_for, flash

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
