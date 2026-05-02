import os
import sys
import time
import threading
from flask import Blueprint, render_template, request, jsonify, current_app, abort, session
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.file_manager import FileManager
from .....security import RateLimiter, InputValidator, validate_input, CSRFProtection, SecurityLogger
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
    
    # CSRF protection
    csrf_token = request.form.get("_csrf_token")
    if not csrf_token or not CSRFProtection.validate_token(csrf_token):
        SecurityLogger.log_unauthorized_access(
            session.get('user', 'unknown'),
            '/admin/settings',
            request.remote_addr
        )
        abort(403)
    
    # Rate limit settings updates - max 10 per minute
    if rate_limiter.is_rate_limited(f"settings_update_{request.remote_addr}"):
        SecurityLogger.log_rate_limit_exceeded('/admin/settings', request.remote_addr)
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


# CACHE: Flush all caches
@admin_settings_bp.route("/cache/flush", methods=["POST"])
@auth.require_admin
def flush_cache():
    """Flush all application caches"""
    try:
        from lib.cache_utils import clear_all_caches, get_cache_stats
        
        # Get stats before clearing
        stats_before = get_cache_stats()
        
        # Clear all caches
        clear_all_caches()
        
        return jsonify({
            "status": "ok",
            "message": "All caches flushed successfully",
            "stats_before": stats_before
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# CACHE: Get cache statistics
@admin_settings_bp.route("/cache/stats", methods=["GET"])
@auth.require_admin
def cache_stats():
    """Get cache statistics"""
    try:
        from lib.cache_utils import get_cache_stats
        stats = get_cache_stats()
        return jsonify({
            "status": "ok",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# UPDATE: Check for updates
@admin_settings_bp.route("/update/check", methods=["GET"])
@auth.require_admin
def check_update():
    """Check for available updates"""
    try:
        from updater.updater import auto_update
        result = auto_update()
        
        # Load the version.json to get update status
        version_file = os.path.join(BASE_PATH, "data", "version.json")
        version_info = {"requires_update": False, "latest_version": "unknown", "current_version": "unknown"}
        
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                version_info = json.load(f)
        
        return jsonify({
            "status": "ok",
            "update_available": version_info.get("requires_update", False),
            "current_version": version_info.get("current_version", "unknown"),
            "latest_version": version_info.get("latest_version", "unknown"),
            "message": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# UPDATE: Get current version info
@admin_settings_bp.route("/update/status", methods=["GET"])
@auth.require_admin
def update_status():
    """Get current version status"""
    try:
        version_file = os.path.join(BASE_PATH, "data", "version.json")
        version_info = {"requires_update": False, "latest_version": "unknown", "current_version": "unknown"}
        
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                version_info = json.load(f)
        
        return jsonify({
            "status": "ok",
            "version": version_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# UPDATE: Download and install update
@admin_settings_bp.route("/update/install", methods=["POST"])
@auth.require_admin
def install_update():
    """Download and install the latest update"""
    import requests
    import zipfile
    import tempfile
    import shutil
    
    # Rate limit update installations - max 1 per hour
    if rate_limiter.is_rate_limited(f"update_install_{request.remote_addr}", max_requests=1, window_seconds=3600):
        return jsonify({
            "status": "error",
            "message": "Update installation rate limited. Please wait 1 hour between installations."
        }), 429
    
    try:
        # Read license key
        license_file = os.path.join(BASE_PATH, "data", "license.txt")
        if not os.path.exists(license_file):
            return jsonify({
                "status": "error",
                "message": "License file not found. Please ensure data/license.txt exists."
            }), 400
        
        with open(license_file, "r", encoding="utf-8") as f:
            license_key = f.read().strip()
        
        if not license_key:
            return jsonify({
                "status": "error",
                "message": "License key is empty. Please check data/license.txt."
            }), 400
        
        # Get current version
        version_file = os.path.join(BASE_PATH, "data", "version.json")
        current_version = "0.1.0"  # Default fallback
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                version_data = json.load(f)
                current_version = version_data.get("current_version", "0.1.0")
        
        # Download update
        update_url = f"https://latinai.ch/wp-json/shoplicensegateway/update?version={current_version}&license_key={license_key}"
        
        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "update.zip")
            
            # Download the ZIP file
            response = requests.get(update_url, timeout=300)  # 5 minute timeout
            response.raise_for_status()
            
            # Save ZIP file
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            # Extract ZIP file
            extract_path = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Get list of files in the extracted directory
            extracted_files = []
            for root, dirs, files in os.walk(extract_path):
                for file in files:
                    rel_path = os.path.relpath(os.path.join(root, file), extract_path)
                    extracted_files.append(rel_path)
            
            # Copy files to installation directory
            updated_files = []
            for rel_path in extracted_files:
                source_path = os.path.join(extract_path, rel_path)
                target_path = os.path.join(BASE_PATH, rel_path)
                
                # Create target directory if it doesn't exist
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # Copy file (this will overwrite existing files)
                shutil.copy2(source_path, target_path)
                updated_files.append(rel_path)
            
            # Log the update
            SecurityLogger.log_config_change(
                session.get('user', 'unknown'),
                'system_update',
                current_version,
                f"Updated {len(updated_files)} files"
            )
            
            return jsonify({
                "status": "ok",
                "message": f"Successfully updated {len(updated_files)} files",
                "files_updated": updated_files,
                "restart_required": True
            })
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to download update: {str(e)}"
        }), 500
    except zipfile.BadZipFile as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid ZIP file received: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Update installation failed: {str(e)}"
        }), 500