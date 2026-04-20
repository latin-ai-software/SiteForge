import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from .....netdefense.auth.provider import AuthManager
from .....data.media_manager import MediaManager

admin_media_bp = Blueprint("admin_media", __name__, url_prefix="/admin/media")

# Auth and Media Manager
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)
media_manager = MediaManager(BASE_PATH)


@admin_media_bp.route("/", methods=["GET"])
@auth.require_admin
def media_library():
    """View all uploaded media files"""
    files = media_manager.get_usage_summary()
    return render_template("admin/media/index.html", files=files)


@admin_media_bp.route("/file/<filename>", methods=["GET"])
@auth.require_admin
def file_details(filename):
    """Get details about a specific file"""
    info = media_manager.get_file_info(filename)
    if not info:
        abort(404)
    return render_template("admin/media/details.html", file_info=info)


@admin_media_bp.route("/delete/<filename>", methods=["POST"])
@auth.require_admin
def delete_file(filename):
    """Delete a file"""
    success, msg = media_manager.delete_file(filename)
    if success:
        return jsonify({"status": "deleted", "message": msg}), 200
    else:
        return jsonify({"error": msg}), 400
