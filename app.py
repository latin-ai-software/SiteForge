def create_app(config_name=None):
    """Application factory pattern for modern Flask apps."""
    import sys
    import importlib.util
    from flask import Flask, render_template, send_from_directory, Response, redirect, url_for
    from werkzeug.middleware.proxy_fix import ProxyFix
    import json
    import lib.netdefense.check
    from lib.security import add_security_headers, RateLimiter, ConfigEncryption, SecureConfig
    from lib.security.encrypted_files import init_encryption
    from lib.routes.setup.index import setup_bp, is_setup_completed
    from lib.routes.create.post.index import post_create_bp
    from lib.routes.root.index import root_bp
    from lib.routes.admin.manage.templates.index import admin_templates_bp
    from lib.routes.admin.manage.posts.index import admin_posts_bp
    from lib.routes.admin.manage.users.index import admin_users_bp
    from lib.routes.admin.manage.analytics.index import admin_analytics_bp
    from lib.routes.admin.manage.settings.index import admin_settings_bp
    from lib.routes.admin.manage.media.index import admin_media_bp
    from lib.routes.root.auth import auth_bp
    from lib.routes.data.youtube import youtube_bp
    from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
    import os
    from datetime import datetime

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, use environment variables only

    # Initialize Flask app
    app = Flask(__name__)

    # Get base path for security configuration
    base_path = os.path.abspath(os.path.dirname(__file__))

    # Apply secure configuration
    secure_config = SecureConfig.get_config(base_path)
    app.config.update(secure_config)

    # Apply modern configuration
    from config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Trust X-Forwarded headers from proxies (e.g., Cloudflare tunnel)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1, x_port=1)

    # Initialize encryption system
    init_encryption(base_path)
    config_encryption = ConfigEncryption(base_path)

    # Add security headers to all responses
    add_security_headers(app)

    # Setup modern logging
    from logging_config import setup_logging
    setup_logging(app)

    # Initialize rate limiter
    rate_limiter = RateLimiter(base_path)

    # Periodic cleanup task (in real deployment, use celery or similar)
    import threading
    import logging
    import time

    logger = logging.getLogger(__name__)

    def cleanup_rate_limits():
        while True:
            time.sleep(3600)  # Cleanup every hour
            try:
                rate_limiter.cleanup_old_data()
            except Exception as e:
                logger.error(f"Error during rate limit cleanup: {e}", exc_info=True)

    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_rate_limits, daemon=True)
    cleanup_thread.start()

    from updater.update_loop import start_update_loop
    start_update_loop()

    # Register blueprints
    app.register_blueprint(setup_bp)
    app.register_blueprint(post_create_bp)
    app.register_blueprint(root_bp)
    app.register_blueprint(admin_templates_bp)
    app.register_blueprint(admin_posts_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_settings_bp)
    app.register_blueprint(admin_media_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_analytics_bp)
    from lib.routes.admin.manage.backup import backup_bp
    app.register_blueprint(backup_bp)
    app.register_blueprint(youtube_bp)

    # Global variable to track loaded plugins
    loaded_plugins = set()
    available_plugins = set()
    from lib.routes.admin.manage.theme_creator import theme_creator_bp
    app.register_blueprint(theme_creator_bp)

    from lib.data.settings import get_theme
    from lib.security import CSRFProtection

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}, 200

    # Load plugins (keeping existing logic)
    load_plugins(app)

    # Setup check middleware
    @app.before_request
    def check_setup_required():
        """Check if setup is required and redirect if necessary"""
        from flask import request

        # Allow setup routes, static files, and uploads without setup check
        if (request.path.startswith('/setup') or
            request.path.startswith('/static') or
            request.path.startswith('/uploads') or
            request.path.startswith('/favicon.ico') or
            request.path.startswith('/robots.txt')):
            return

        # Check if setup has been completed
        if not is_setup_completed(base_path):
            return redirect(url_for('setup.setup_page'))

    return app

# For backward compatibility, keep original code below
import sys
import importlib.util
from flask import Flask, render_template, send_from_directory, Response, redirect, url_for
import requests
from werkzeug.middleware.proxy_fix import ProxyFix
import json
import lib.netdefense.check
from lib.security import add_security_headers, RateLimiter, ConfigEncryption, SecureConfig
from lib.security.encrypted_files import init_encryption
from lib.routes.setup.index import setup_bp, is_setup_completed
from lib.routes.create.post.index import post_create_bp
from lib.routes.root.index import root_bp
from lib.routes.admin.manage.templates.index import admin_templates_bp
from lib.routes.admin.manage.posts.index import admin_posts_bp
from lib.routes.admin.manage.users.index import admin_users_bp
from lib.routes.admin.manage.analytics.index import admin_analytics_bp
from lib.routes.admin.manage.settings.index import admin_settings_bp
from lib.routes.admin.manage.media.index import admin_media_bp
from lib.routes.root.auth import auth_bp
from lib.routes.data.youtube import youtube_bp
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
import os
from datetime import datetime

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only

# Initialize Flask app
app = Flask(__name__)

# Get base path for security configuration
base_path = os.path.abspath(os.path.dirname(__file__))

# Apply secure configuration
secure_config = SecureConfig.get_config(base_path)
app.config.update(secure_config)

# Trust X-Forwarded headers from proxies (e.g., Cloudflare tunnel)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Initialize encryption system
init_encryption(base_path)
config_encryption = ConfigEncryption(base_path)

# Add security headers to all responses
add_security_headers(app)

# Initialize rate limiter
rate_limiter = RateLimiter(base_path)

# Periodic cleanup task (in real deployment, use celery or similar)
import threading
import logging
import time

logger = logging.getLogger(__name__)

def cleanup_rate_limits():
    while True:
        time.sleep(3600)  # Cleanup every hour
        try:
            rate_limiter.cleanup_old_data()
        except Exception as e:
            logger.error(f"Error during rate limit cleanup: {e}", exc_info=True)

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_rate_limits, daemon=True)
cleanup_thread.start()

from updater.update_loop import start_update_loop
start_update_loop()

# Register setup blueprint first (before other routes)
app.register_blueprint(setup_bp)

app.register_blueprint(post_create_bp)
app.register_blueprint(root_bp)
app.register_blueprint(admin_templates_bp)
app.register_blueprint(admin_posts_bp)
app.register_blueprint(admin_users_bp)
app.register_blueprint(admin_settings_bp)
app.register_blueprint(admin_media_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_analytics_bp)
from lib.routes.admin.manage.backup import backup_bp
app.register_blueprint(backup_bp)
app.register_blueprint(youtube_bp)

# Global variable to track loaded plugins
loaded_plugins = set()
available_plugins = set()
from lib.routes.admin.manage.theme_creator import theme_creator_bp
app.register_blueprint(theme_creator_bp)


from lib.data.settings import get_theme
from lib.security import CSRFProtection

@app.context_processor
def inject_template_context():
    """Inject commonly used values into all templates"""
    return {
        "active_theme": get_theme(),
        "csrf_token": CSRFProtection.generate_token
    }


# Load optional plugins from plugins/ directory

def load_plugins(application):
    global loaded_plugins, available_plugins
    plugins_dir = os.path.join(application.root_path, "plugins")
    if not os.path.isdir(plugins_dir):
        return

    # Load settings to check enabled plugins (use encryption manager for decryption)
    settings_file = os.path.join(application.root_path, "data", "settings.json")
    settings = {}
    if os.path.exists(settings_file):
        try:
            settings = config_encryption.encryption.load_json_file(settings_file, auto_decrypt=True)
            if settings is None:
                settings = {}
        except Exception as e:
            print(f"Warning: Could not load settings.json: {e}")
            settings = {}
    enabled_plugins = settings.get("enabled_plugins", {})

    for item in os.listdir(plugins_dir):
        plugin_dir = os.path.join(plugins_dir, item)
        if not os.path.isdir(plugin_dir) or item.startswith('_'):
            continue

        plugin_file = os.path.join(plugin_dir, f"{item}.py")
        if not os.path.isfile(plugin_file):
            continue

        available_plugins.add(item)

        # Check if plugin is enabled
        if not enabled_plugins.get(item, False):
            continue

        spec = importlib.util.spec_from_file_location(f"plugins.{item}.{item}", plugin_file)
        if not spec or not spec.loader:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Plugin load failed for {item}: {e}")
            continue

        # Track loaded plugin
        loaded_plugins.add(item)

        if hasattr(module, 'plugin_blueprint'):
            application.register_blueprint(module.plugin_blueprint)
        if hasattr(module, 'git_http_blueprint'):
            application.register_blueprint(module.git_http_blueprint)
        if hasattr(module, 'init_plugin'):
            try:
                module.init_plugin(application)
            except Exception as e:
                print(f"Plugin init failed for {item}: {e}")

    # Store available plugins on app
    application.available_plugins = available_plugins

load_plugins(app)

def is_plugin_loaded(plugin_name):
    return plugin_name in loaded_plugins

def is_plugin_available(plugin_name):
    return plugin_name in available_plugins

# Make plugin check available to templates
@app.context_processor
def inject_plugin_check():
    return dict(is_plugin_loaded=is_plugin_loaded, is_plugin_available=is_plugin_available)

# Setup check middleware - redirect to setup if not completed
@app.before_request
def check_setup_required():
    """Check if setup is required and redirect if necessary"""
    from flask import request
    
    # Allow setup routes, static files, and uploads without setup check
    if (request.path.startswith('/setup') or 
        request.path.startswith('/static') or 
        request.path.startswith('/uploads') or
        request.path.startswith('/favicon.ico') or
        request.path.startswith('/robots.txt')):
        return
    
    # Check if setup has been completed
    if not is_setup_completed(base_path):
        return redirect(url_for('setup.setup_page'))

# Analytics middleware
@app.before_request
def check_rate_limits():
    """DDOS protection - rate limit by IP address"""
    from flask import request, abort
    
    ip = request.remote_addr
    
    # Allow higher limits for static files and health checks
    if request.path.startswith('/static') or request.path.startswith('/uploads'):
        max_requests = 1000
    elif request.path.startswith('/admin'):
        max_requests = 100
    else:
        max_requests = 300
    
    if rate_limiter.is_rate_limited(f"ip_{ip}"):
        # Log potential DDOS attempt
        print(f"Rate limit exceeded for IP: {ip}, path: {request.path}")
        abort(429)  # Too Many Requests


@app.before_request
def track_visitor():
    from flask import request, session
    import json
    from datetime import datetime

    # Skip tracking for admin routes, static files, and API calls
    if request.path.startswith('/admin') or request.path.startswith('/static') or request.path.startswith('/uploads') or request.path.startswith('/consent'):
        return

    # Check if analytics is enabled
    settings_file = os.path.join(app.root_path, 'data', 'settings.json')
    if not os.path.exists(settings_file):
        return

    with open(settings_file, 'r', encoding='utf-8') as f:
        settings = json.load(f)

    # If analytics is enabled, cookie consent is automatically required
    if not settings.get('enable_analytics', False) or not (settings.get('require_cookie_consent', False) or settings.get('enable_analytics', False)):
        return

    # Check if user has consented to analytics cookies (check both session and cookie)
    has_consent = session.get('analytics_consent', False) or request.cookies.get('analytics_consent') == 'true'
    if not has_consent:
        return

    # Track the visitor
    analytics_file = os.path.join(app.root_path, 'data', 'analytics.json')
    analytics = {"visitors": []}

    if os.path.exists(analytics_file):
        with open(analytics_file, 'r', encoding='utf-8') as f:
            analytics = json.load(f)

    visitor = {
        "timestamp": datetime.now().isoformat(),
        "ip": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', ''),
        "path": request.path,
        "method": request.method
    }

    analytics["visitors"].append(visitor)

    # Keep only last 10000 visitors to prevent file from growing too large
    if len(analytics["visitors"]) > 10000:
        analytics["visitors"] = analytics["visitors"][-10000:]

    with open(analytics_file, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=4, default=str)

    print(f"Analytics: Tracked visitor to {request.path}")  # Debug logging

# Analytics consent endpoint
@app.route('/consent/analytics', methods=['POST'])
def analytics_consent():
    from flask import request, session, jsonify, make_response
    data = request.get_json()
    if data and data.get('consent'):
        session['analytics_consent'] = True
        # Also set a cookie for client-side persistence
        resp = make_response(jsonify({'status': 'ok'}))
        resp.set_cookie('analytics_consent', 'true', max_age=365*24*60*60)  # 1 year
        return resp
    return jsonify({'status': 'ok'})

# Route for serving uploaded files (admin only)
@app.route('/data/uploads/<filename>')
def uploaded_file(filename):
    from flask import session, abort
    
    # Check if user is logged in and is an administrator
    if 'user' not in session:
        abort(403)  # Forbidden
    
    auth_manager = IdentitasAuthManager(app.root_path)
    if auth_manager.get_user_role(session['user']) != 'administrator':
        abort(403)  # Forbidden
    
    uploads_dir = os.path.join(app.root_path, 'data', 'uploads')
    return send_from_directory(uploads_dir, filename)

# Legacy route for backward compatibility (public access, no auth)
@app.route('/uploads/<filename>')
def uploaded_file_legacy(filename):
    uploads_dir = os.path.join(app.root_path, 'data', 'uploads')
    return send_from_directory(uploads_dir, filename)


@app.route('/favicon.ico')
def favicon():
    settings_file = os.path.join(app.root_path, 'data', 'settings.json')
    favicon_filename = None
    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            favicon_filename = settings.get('favicon_filename')

    if favicon_filename:
        uploads_dir = os.path.join(app.root_path, 'data', 'uploads')
        return send_from_directory(uploads_dir, favicon_filename)

    fallback_path = os.path.join(app.static_folder, 'favicon.ico')
    if os.path.exists(fallback_path):
        return send_from_directory(app.static_folder, 'favicon.ico')

    return '', 404
@app.template_filter("datetimeformat")
def datetimeformat(value):
    if not value:
        return "Unbekannt"
    return datetime.fromtimestamp(value).strftime("%d.%m.%Y, %H:%M")


@app.route('/robots.txt')
def robots_txt():
    settings_file = os.path.join(app.root_path, 'data', 'settings.json')
    allow_robot_indexing = False
    robot_user_agents = ''

    if os.path.exists(settings_file):
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            allow_robot_indexing = settings.get('allow_robot_indexing', False)
            robot_user_agents = settings.get('robot_user_agents', '').strip()

    if allow_robot_indexing:
        agents = [line.strip() for line in robot_user_agents.splitlines() if line.strip()] or ['*']
        lines = []
        for agent in agents:
            lines.append(f'User-agent: {agent}')
            lines.append('Allow: /')
        body = '\n'.join(lines) + '\n'
    else:
        body = 'User-agent: *\nDisallow: /\n'

    return Response(body, mimetype='text/plain')


# Security error handlers
@app.errorhandler(429)
def rate_limit_error(error):
    """Handle rate limit exceeded"""
    return render_template('error.html', 
                         error_code=429, 
                         error_message='Too many requests. Please try again later.'), 429


@app.errorhandler(403)
def forbidden_error(error):
    """Handle forbidden access"""
    return render_template('error.html', 
                         error_code=403, 
                         error_message='Access denied.'), 403


@app.errorhandler(404)
def not_found_error(error):
    """Handle not found"""
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page not found.'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle server errors"""
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal server error.'), 500


def handle_cli():
    """
    CLI‑Argumente prüfen:
    --create-admin <name> -p <passwort> [--role <role>]
    """
    if "--create-admin" in sys.argv:
        try:
            name_index = sys.argv.index("--create-admin") + 1
            username = sys.argv[name_index]
        except Exception:
            print("Fehler: Benutzername fehlt nach --create-admin")
            sys.exit(1)

        if "-p" not in sys.argv:
            print("Fehler: Passwort fehlt. Nutze: --create-admin <name> -p <passwort> [--role <role>]")
            sys.exit(1)

        try:
            pass_index = sys.argv.index("-p") + 1
            password = sys.argv[pass_index]
        except Exception:
            print("Fehler: Passwort fehlt nach -p")
            sys.exit(1)

        role = "administrator"  # default
        if "--role" in sys.argv:
            try:
                role_index = sys.argv.index("--role") + 1
                role = sys.argv[role_index]
            except Exception:
                print("Fehler: Rolle fehlt nach --role")
                sys.exit(1)

        base_path = os.path.dirname(os.path.abspath(__file__))
        auth = IdentitasAuthManager(base_path)

        ok, msg = auth.create_user(username, password, role)
        print(msg)

        # Admin erzwingen
        if ok and username != "admin":
            print("Hinweis: Nur der Benutzername 'admin' gilt als Administrator.")
            print("Wenn du einen Admin willst, nutze:")
            print("   --create-admin admin -p <passwort>")

        sys.exit(0)


import os

def read_license_key():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    license_file = os.path.join(base_dir, "data", "license.txt")

    if not os.path.exists(license_file):
        raise FileNotFoundError("license.txt not found")

    with open(license_file, "r") as f:
        return f.read().strip()
    import requests

def is_license_valid(license_key):
    url = f"https://latinai.ch/wp-json/shoplicensegateway/license/validate/{license_key}"

    try:
        response = requests.get(url, timeout=5)
    except Exception:
        return False

    # Prüfen ob JSON
    try:
        data = response.json()
    except ValueError:
        return False

    # Gateway gibt {"status": "valid"} zurück
    return data.get("status") == "valid"
def ensure_license_valid():
    license_key = read_license_key()

    if not is_license_valid(license_key):
        print("❌ Lizenz ungültig — Anwendung wird beendet.")
        exit(1)

    print("✔ Lizenz gültig — Anwendung startet.")
if __name__ == "__main__":
    ensure_license_valid()

    handle_cli()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--cert", type=str, help="Path to SSL certificate")
    parser.add_argument("--key", type=str, help="Path to SSL private key")

    args = parser.parse_args()

    # SSL aktiv?
    ssl_context = None
    if args.ssl:
        if not args.cert or not args.key:
            raise ValueError("SSL requires --cert and --key")
        ssl_context = (args.cert, args.key)

    app.run(
        debug=args.debug,
        port=443,
        ssl_context=ssl_context
    )