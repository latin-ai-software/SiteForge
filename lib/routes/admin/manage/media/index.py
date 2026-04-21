import os
import time
from flask import Blueprint, render_template, request, jsonify, abort
from .....netdefense.auth.provider import AuthManager
from .....data.media_manager import MediaManager

# Blueprint-Konfiguration
admin_media_bp = Blueprint("admin_media", __name__, url_prefix="/admin/media")

# Basis-Pfad und Manager
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)
media_manager = MediaManager(BASE_PATH)


@admin_media_bp.route("/", methods=["GET"])
@auth.require_admin
def media_library():
    """
    Media Library mit Filtern:
    - q: Name enthält
    - type: Dateiendung
    - date: 'today', '7d', '30d'
    """

    # Filter-Parameter
    q = request.args.get("q", "").strip().lower()
    filetype = request.args.get("type", "").strip().lower()
    date_filter = request.args.get("date", "").strip().lower()

    # Alle Dateien holen
    files = media_manager.get_usage_summary() or []
    filtered_files = []

    now = time.time()

    for f in files:
        name = str(f.get("filename", "")).lower()
        name = str(f.get("filename", "")).lower()
        ext = name.split(".")[-1] if "." in name else ""
        path = f.get("path")

        # Upload-Datum aus Dateisystem holen
        try:
            uploaded_ts = os.path.getmtime(path)
        except:
            uploaded_ts = None

        f["uploaded_at"] = uploaded_ts

        # Name-Filter
        if q and q not in name:
            continue

        # Typ-Filter
        if filetype and ext != filetype:
            continue

        # Datum-Filter
        if date_filter and uploaded_ts:
            age = now - uploaded_ts

            if date_filter == "today":
                if age > 86400:
                    continue

            elif date_filter.endswith("d"):
                days = int(date_filter.replace("d", ""))
                if age > days * 86400:
                    continue

        filtered_files.append(f)

    return render_template(
        "admin/media/index.html",
        files=filtered_files,
        q=q,
        filetype=filetype,
        date_filter=date_filter
    )


@admin_media_bp.route("/file/<filename>", methods=["GET"])
@auth.require_admin
def file_details(filename):
    """Details zu einer Datei anzeigen"""
    info = media_manager.get_file_info(filename)
    if not info:
        abort(404)
    return render_template("admin/media/details.html", file_info=info)


@admin_media_bp.route("/delete/<filename>", methods=["POST"])
@auth.require_admin
def delete_file(filename):
    """Datei löschen"""
    success, msg = media_manager.delete_file(filename)
    if success:
        return jsonify({"status": "deleted", "message": msg}), 200
    else:
        return jsonify({"error": msg}), 400
@admin_media_bp.route("/rename/<filename>", methods=["POST"])
@auth.require_admin
def rename_file(filename):
    """Rename a file"""
    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        return jsonify({"error": "Neuer Dateiname fehlt"}), 400

    success, msg = media_manager.rename_file(filename, new_name)

    if success:
        return jsonify({"status": "renamed", "message": msg, "new_name": new_name}), 200
    else:
        return jsonify({"error": msg}), 400
