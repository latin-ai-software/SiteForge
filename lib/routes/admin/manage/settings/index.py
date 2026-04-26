import os
import sys
import time
import threading
from flask import Blueprint, render_template, request, jsonify, current_app, abort
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.file_manager import FileManager
from .....security import RateLimiter, InputValidator, validate_input
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
auth = IdentitasAuthManager(BASE_PATH)
file_manager = FileManager(BASE_PATH)
rate_limiter = RateLimiter(BASE_PATH)

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
    
    # Rate limit settings updates - max 10 per minute
    if rate_limiter.is_rate_limited(f"settings_update_{request.remote_addr}"):
        abort(429)
    
    # Input validation and sanitization
    site_title = validate_input(request.form.get("site_title", "SiteForge"), max_length=255)
    site_description = validate_input(request.form.get("site_description", ""), max_length=1000)
    domain = validate_input(request.form.get("domain", ""), max_length=255)
    
    try:
        posts_per_page = int(request.form.get("posts_per_page", 10))
        analytics_period_days = int(request.form.get("analytics_period_days", 30))
        ses_smtp_port = int(request.form.get("ses_smtp_port", 587) or 587)
        
        if not (1 <= posts_per_page <= 100):
            return jsonify({"status": "error", "message": "Posts per page must be 1-100"}), 400
        if not (1 <= analytics_period_days <= 365):
            return jsonify({"status": "error", "message": "Analytics period must be 1-365 days"}), 400
        if not (1 <= ses_smtp_port <= 65535):
            return jsonify({"status": "error", "message": "Invalid SMTP port"}), 400
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid numeric values"}), 400
    
    # Validate email if provided
    newsletter_sender_email = request.form.get("newsletter_sender_email", "").strip()
    if newsletter_sender_email and not InputValidator.validate_email(newsletter_sender_email):
        return jsonify({"status": "error", "message": "Invalid email format"}), 400
    
    # Validate Google Analytics ID format if provided
    analytics_tracking_id = request.form.get("analytics_tracking_id", "").strip()
    if analytics_tracking_id and not analytics_tracking_id.startswith(('G-', 'UA-')):
        return jsonify({"status": "error", "message": "Invalid Google Analytics ID format"}), 400

    settings = {
        "site_title": site_title or "SiteForge",
        "site_description": site_description or "",
        "posts_per_page": posts_per_page,
        "allow_registration": request.form.get("allow_registration") == "on",
        "require_comment_approval": request.form.get("require_comment_approval") == "on",
        "allow_robot_indexing": request.form.get("allow_robot_indexing") == "on",
        "robot_user_agents": validate_input(request.form.get("robot_user_agents", ""), max_length=500) or "",
        "require_cookie_consent": request.form.get("require_cookie_consent") == "on" or request.form.get("enable_analytics") == "on",
        "cookie_consent_message": validate_input(request.form.get("cookie_consent_message", ""), max_length=2000, allowed_chars=['<', '>', '"', "'", '&', ';']) or "",
        "enable_analytics": request.form.get("enable_analytics") == "on",
        "analytics_provider": request.form.get("analytics_provider", "builtin"),
        "analytics_tracking_id": analytics_tracking_id,
        "analytics_period_days": analytics_period_days,
        "embed_favicon_in_html": request.form.get("embed_favicon_in_html") == "on",
        "imprint_enabled": request.form.get("imprint_enabled") == "on",
        "allow_password_change": request.form.get("allow_password_change") == "on",
        "domain": domain or "",
        "header_background_enabled": request.form.get("header_background_enabled") == "on",
        "setup_completed": True,
        "show_social_links": request.form.get("show_social_links") == "on",
        "twitter_handle": validate_input(request.form.get("twitter_handle", ""), max_length=100) or "",
        "facebook_page": validate_input(request.form.get("facebook_page", ""), max_length=255) or "",
    }

    # Load existing settings to preserve secret fields when left blank
    available_plugins = getattr(current_app, 'available_plugins', set())
    settings["enabled_plugins"] = {}
    old_settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            old_settings = json.load(f)
    old_enabled_plugins = old_settings.get("enabled_plugins", {})

    # Preserve SES password if the admin leaves the field blank
    ses_password = request.form.get("ses_smtp_password", "").strip()
    if not ses_password:
        ses_password = old_settings.get("ses_smtp_password", "")

    settings.update({
        "newsletter_enabled": request.form.get("newsletter_enabled") == "on",
        "newsletter_sender_email": newsletter_sender_email,
        "ses_smtp_host": validate_input(request.form.get("ses_smtp_host", ""), max_length=255) or "",
        "ses_smtp_port": ses_smtp_port,
        "ses_smtp_username": validate_input(request.form.get("ses_smtp_username", ""), max_length=255) or "",
        "ses_smtp_password": ses_password,
        "youtube_channel_id": validate_input(request.form.get("youtube_channel_id", ""), max_length=255) or "",
    })

    plugin_changed = False
    for plugin in available_plugins:
        enabled = request.form.get(f"enable_{plugin}") == "on"
        settings["enabled_plugins"][plugin] = enabled
        if old_enabled_plugins.get(plugin, False) != enabled:
            plugin_changed = True

    # Imprint-Datei hochladen (validate HTML file)
    imprint_file = request.files.get("imprint")
    if imprint_file and imprint_file.filename:
        if not imprint_file.filename.endswith('.html'):
            return jsonify({"status": "error", "message": "Imprint must be an HTML file"}), 400
        
        target_path = os.path.join(current_app.root_path, "static", "imprint.html")
        imprint_file.save(target_path)

    # Favicon upload (validate image file)
    favicon_file = request.files.get("favicon")
    if favicon_file and favicon_file.filename:
        allowed_image_ext = {'png', 'jpg', 'jpeg', 'gif', 'ico'}
        file_ext = favicon_file.filename.rsplit('.', 1)[1].lower() if '.' in favicon_file.filename else ''
        if file_ext not in allowed_image_ext:
            return jsonify({"status": "error", "message": "Favicon must be an image file"}), 400
        
        target_path = os.path.join(current_app.root_path, "static", "favicon.ico")
        favicon_file.save(target_path)
        settings["favicon_filename"] = "favicon.ico"
        settings["favicon_original_name"] = favicon_file.filename
    
    # Header background upload (validate JPG)
    header_bg_file = request.files.get("header-background")
    if header_bg_file and header_bg_file.filename:
        if not header_bg_file.filename.lower().endswith(('.jpg', '.jpeg')):
            return jsonify({"status": "error", "message": "Header background must be a JPG file"}), 400
        
        target_path = os.path.join(current_app.root_path, "static", "header-background.jpg")
        header_bg_file.save(target_path)
        settings["header_background_filename"] = "header-background.jpg"
        settings["header_background_original_name"] = header_bg_file.filename

    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

    if plugin_changed:
        schedule_restart()
        return jsonify({"status": "ok", "restart": True})

    return jsonify({"status": "ok"})


# Encryption management endpoints
@admin_settings_bp.route("/encryption/status", methods=["GET"])
@auth.require_admin
def encryption_status():
    """Get current encryption status"""
    from ...security import ConfigEncryption
    config_enc = ConfigEncryption(BASE_PATH)
    status = config_enc.get_status()
    return jsonify(status)


@admin_settings_bp.route("/encryption/enable", methods=["POST"])
@auth.require_admin
def encryption_enable():
    """Enable encryption for all config files"""
    from ...security import ConfigEncryption
    
    # Rate limit encryption changes - max 1 per minute
    if rate_limiter.is_rate_limited(f"encryption_change_{request.remote_addr}"):
        abort(429)
    
    try:
        config_enc = ConfigEncryption(BASE_PATH)
        results = config_enc.enable_all()
        
        success_count = sum(1 for success, _ in results.values() if success)
        return jsonify({
            "status": "ok",
            "message": f"Encryption enabled for {success_count} files",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@admin_settings_bp.route("/encryption/disable", methods=["POST"])
@auth.require_admin
def encryption_disable():
    """Disable encryption for all config files (DANGEROUS)"""
    from ...security import ConfigEncryption
    
    # Rate limit encryption changes - max 1 per minute
    if rate_limiter.is_rate_limited(f"encryption_change_{request.remote_addr}"):
        abort(429)
    
    # Require confirmation
    confirm = request.form.get("confirm_disable") == "true"
    if not confirm:
        return jsonify({
            "status": "error",
            "message": "Must confirm disabling encryption by setting confirm_disable=true"
        }), 400
    
    try:
        config_enc = ConfigEncryption(BASE_PATH)
        results = config_enc.disable_all()
        
        success_count = sum(1 for success, _ in results.values() if success)
        return jsonify({
            "status": "ok",
            "message": f"Encryption disabled for {success_count} files",
            "results": results
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500