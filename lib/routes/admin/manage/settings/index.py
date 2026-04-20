import os
import sys
import time
import threading
from flask import Blueprint, render_template, request, jsonify, current_app
from .....netdefense.auth.provider import AuthManager
from .....data.file_manager import FileManager
import json

admin_settings_bp = Blueprint("admin_settings", __name__, url_prefix="/admin/settings")

def schedule_restart(delay=0.5):
    def restart():
        time.sleep(delay)
        python = sys.executable
        os.execv(python, [python] + sys.argv)
    t = threading.Thread(target=restart, daemon=True)
    t.start()

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)
file_manager = FileManager(BASE_PATH)

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

    # Get available plugins
    available_plugins = getattr(current_app, 'available_plugins', set())
    return render_template("admin/settings/index.html", settings=settings, available_plugins=list(available_plugins))

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
        "require_comment_approval": request.form.get("require_comment_approval") == "on",
        "allow_robot_indexing": request.form.get("allow_robot_indexing") == "on",
        "robot_user_agents": request.form.get("robot_user_agents", "").strip(),
        "require_cookie_consent": request.form.get("require_cookie_consent") == "on" or request.form.get("enable_analytics") == "on",  # Auto-enable if analytics is enabled
        "cookie_consent_message": request.form.get("cookie_consent_message", "").strip(),
        "enable_analytics": request.form.get("enable_analytics") == "on",
        "analytics_provider": request.form.get("analytics_provider", "builtin"),
        "analytics_tracking_id": request.form.get("analytics_tracking_id", "").strip(),
        "analytics_period_days": int(request.form.get("analytics_period_days", 30)),
        "embed_favicon_in_html": request.form.get("embed_favicon_in_html") == "on",
        "imprint_enabled": request.form.get("imprint_enabled") == "on",
        "allow_password_change": request.form.get("allow_password_change") == "on",
        "domain": request.form.get("domain", "").strip()
    }

    # Handle enabled plugins dynamically
    available_plugins = getattr(current_app, 'available_plugins', set())
    settings["enabled_plugins"] = {}
    old_settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            old_settings = json.load(f)
    old_enabled_plugins = old_settings.get("enabled_plugins", {})

    plugin_changed = False
    for plugin in available_plugins:
        enabled = request.form.get(f"enable_{plugin}") == "on"
        settings["enabled_plugins"][plugin] = enabled
        if old_enabled_plugins.get(plugin, False) != enabled:
            plugin_changed = True

    # Imprint-Datei hochladen
    imprint_file = request.files.get("imprint")
    if imprint_file and imprint_file.filename:
        target_path = os.path.join(current_app.root_path, "static", "imprint.html")

        # Datei speichern/überschreiben
        imprint_file.save(target_path)

    favicon_file = request.files.get("favicon")
    if favicon_file and favicon_file.filename:
        # Zielpfad: static/favicon.ico
        target_path = os.path.join(current_app.root_path, "static", "favicon.ico")

        # Datei speichern/überschreiben
        favicon_file.save(target_path)

        # In den Settings speichern wir nur den Namen, falls du ihn irgendwo anzeigen willst
        settings["favicon_filename"] = "favicon.ico"
        settings["favicon_original_name"] = favicon_file.filename

    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

    if plugin_changed:
        schedule_restart()
        return jsonify({"status": "ok", "restart": True})

    return jsonify({"status": "ok"})