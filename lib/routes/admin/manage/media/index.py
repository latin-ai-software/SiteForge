import os
import time
from flask import Blueprint, render_template, request, jsonify, abort
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.media_manager import MediaManager

admin_media_bp = Blueprint("admin_media", __name__, url_prefix="/admin/media")

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)
media_manager = MediaManager(BASE_PATH)


@admin_media_bp.route("/", methods=["GET"])
@auth.require_admin
def media_library():
    q = request.args.get("q", "").strip().lower()
    filetype = request.args.get("type", "").strip().lower()
    date_filter = request.args.get("date", "").strip().lower()

    files = media_manager.get_usage_summary() or []
    filtered_files = []

    now = time.time()

    for f in files:
        name = str(f.get("filename", "")).lower()

        # Dateiendung extrahieren
        ext = name.split(".")[-1] if "." in name else ""

        path = f.get("path")

        # Upload-Datum
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

            if date_filter == "today" and age > 86400:
                continue

            if date_filter.endswith("d"):
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


@admin_media_bp.route("/api/list", methods=["GET"])
@auth.require_role("author")
def api_list_files():
    """API endpoint to get list of available files"""
    files = media_manager.get_usage_summary() or []
    file_list = [
        {
            "filename": f.get("filename"),
            "size": f.get("size"),
            "display": f"{f.get('filename')} ({f.get('size', 0) / 1024:.1f} KB)"
        }
        for f in files
    ]
    return jsonify(file_list)


@admin_media_bp.route("/file/<filename>", methods=["GET"])
@auth.require_admin
def file_details(filename):
    info = media_manager.get_file_info(filename)
    if not info:
        abort(404)
    return render_template("admin/media/details.html", file_info=info)


@admin_media_bp.route("/delete/<filename>", methods=["POST"])
@auth.require_admin
def delete_file(filename):
    success, msg = media_manager.delete_file(filename)
    if success:
        return jsonify({"status": "deleted", "message": msg}), 200
    return jsonify({"error": msg}), 400


@admin_media_bp.route("/rename/<filename>", methods=["POST"])
@auth.require_admin
def rename_file(filename):
    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        return jsonify({"error": "Neuer Dateiname fehlt"}), 400

    success, msg = media_manager.rename_file(filename, new_name)

    if success:
        return jsonify({"status": "renamed", "new_name": new_name}), 200
    return jsonify({"error": msg}), 400
@admin_media_bp.route("/upload", methods=["POST"])
@auth.require_admin
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei erhalten"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Ungültiger Dateiname"}), 400

    # Speichern im Upload-Ordner
    save_path = os.path.join(media_manager.upload_dir, file.filename)
    file.save(save_path)

    return jsonify({"status": "ok"}), 200
