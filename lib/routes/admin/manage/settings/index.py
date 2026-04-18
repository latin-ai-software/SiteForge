import os
from flask import Blueprint, render_template, request, jsonify, current_app
from .....netdefense.auth.provider import AuthManager
import json

admin_settings_bp = Blueprint("admin_settings", __name__, url_prefix="/admin/settings")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)

# SETTINGS: Einstellungen anzeigen
@admin_settings_bp.route("/", methods=["GET"])
@auth.require_admin
def admin_settings_index():
    # Load current settings
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")

    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    return render_template("admin/settings/index.html", settings=settings)

# POST: Einstellungen speichern
@admin_settings_bp.route("/", methods=["POST"])
@auth.require_admin
def save_settings():
    import json

    settings = {
        "site_title": request.form.get("site_title", "LatinMagazine"),
        "site_description": request.form.get("site_description", ""),
        "posts_per_page": int(request.form.get("posts_per_page", 10)),
        "allow_registration": request.form.get("allow_registration") == "on",
        "require_comment_approval": request.form.get("require_comment_approval") == "on"
    }

    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

    return jsonify({"status": "ok"})