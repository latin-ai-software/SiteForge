import os
import sys


def _is_pytest_running():
    """Return True when the app is being imported under pytest or CI test execution."""
    return os.environ.get('PYTEST_CURRENT_TEST') is not None or 'pytest' in sys.modules or os.environ.get('CI', '').lower() == 'true'


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
    from lib.routes.admin.manage.notifications.index import admin_notifications_bp
    from lib.routes.admin.manage.seo.index import admin_seo_bp
    from lib.routes.admin.manage.api_docs.index import admin_api_docs_bp
    from lib.routes.admin.help import admin_help_bp
    from lib.routes.root.auth import auth_bp
    from lib.routes.data.youtube import youtube_bp
    from lib.routes.modmail import modmail_bp
    from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
    import os
    from datetime import datetime
    from flask_translator import Translator

    # Import models to ensure they're registered with SQLAlchemy
    from lib.data import modmail_models, notification_models

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, use environment variables only

    # Initialize Flask app
    app = Flask(__name__)
    app.config['DEFAULT_LANG'] = 'de'
#    app.config['LANG_INITIALIZER'] = 'headers'
    app.config['DEFAULT_MESSAGE'] = 'Translation Error'
    app.config['TRANSLATIONS_PATH'] = 'translations'
    class UTF8Translator(Translator):
        def _get_file_data(self):
            language = self._language or app.config.get('DEFAULT_LANG', 'en')
            translation_file = os.path.join(
                app.root_path,
                app.config['TRANSLATIONS_PATH'],
                f'messages.{language}.yaml'
            )

            with open(translation_file, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

            return data

        def translate(self, key: str, **kwargs):
            if self._language is None:
                self._language = app.config.get('DEFAULT_LANG', 'en')
            return super().translate(key, **kwargs)

    t = UTF8Translator()
    t.init_app(app)
    t._language = app.config.get('DEFAULT_LANG', 'en')
    app.jinja_env.globals['t'] = t.translate
    @app.context_processor
    def inject_translator():
        t._language = t._language or app.config.get('DEFAULT_LANG', 'en')
        return dict(t=t.translate)
    # And how do I make t available in all blueprint's and their templates? 
    # Because otherwise I get jinja2.exceptions.UndefinedError: 't' is undefined when I try to use {{ t("all_posts") }} in templates rendered by Blueprints.
    # The solution is to use a context processor in the main app to inject the translator's 't' function into all templates, including those rendered by Blueprints. This way, you can use {{ t("your_translation_key") }} in any template without needing to import or initialize the translator in each Blueprint separately.
    # How to fix jinja2.exceptions.UndefinedError: 't' is undefined: https://flask-translator.readthedocs.io/en/latest/#usage-in-templates
    # Add the translator's 't' function to the template context
    # And how to do that in Blueprints? Use a context processor
#    @app.context_processor
    #def inject_translator():
    #    return dict(t=translator.t)
    # Get base path for security configuration
    base_path = os.path.abspath(os.path.dirname(__file__))

    # Apply secure configuration
    secure_config = SecureConfig.get_config(base_path)
    app.config.update(secure_config)

    # Apply modern configuration after security defaults so TESTING/configuration wins.
    from config import get_config
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Test mode must never trust spoofed forwarded headers, even if a proxy env value is set.
    is_testing_mode = bool(
        app.config.get('TESTING')
        or os.environ.get('PYTEST_CURRENT_TEST') is not None
        or os.environ.get('CI', '').lower() == 'true'
    )
    trusted_proxy_ips = set() if is_testing_mode else {
        entry.strip()
        for entry in os.environ.get('TRUSTED_PROXY_IPS', '').split(',')
        if entry.strip()
    }
    if trusted_proxy_ips:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1, x_port=1)
    else:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=0, x_host=0, x_prefix=0, x_port=0)

    def get_client_ip():
        """Return the real remote IP unless a configured trusted proxy forwarded the request."""
        from flask import request

        remote_ip = request.remote_addr or 'unknown'
        if is_testing_mode:
            return remote_ip

        forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
        if not forwarded_for or remote_ip not in trusted_proxy_ips:
            return remote_ip

        candidates = [entry.strip() for entry in forwarded_for.split(',') if entry.strip()]
        return candidates[0] if candidates else remote_ip

    if app.config.get('LOAD_BALANCING_ENABLED'):
        try:
            import redis
            from lib.security.cluster_session import RedisSessionInterface
            redis_client = redis.Redis.from_url(app.config.get('REDIS_URL', 'redis://localhost:6379/0'), decode_responses=True)
            redis_client.ping()
            app.session_interface = RedisSessionInterface(redis_client=redis_client, prefix='siteforge:session:')
        except Exception as exc:
            raise RuntimeError(
                'Load balancing mode requires a reachable Redis instance at REDIS_URL. Start Redis or disable LOAD_BALANCING_ENABLED.'
            ) from exc

    # Initialize encryption system
    init_encryption(base_path)
    config_encryption = ConfigEncryption(base_path)

    # Add security headers to all responses
    add_security_headers(app)

    # Setup modern logging
    from logging_config import setup_logging
    setup_logging(app)

    # Initialize rate limiter; use a dedicated test-side store so each app instance starts clean.
    if app.config.get('TESTING'):
        test_limits = os.path.join(base_path, 'data', 'rate_limits_testing.json')
        test_lockouts = os.path.join(base_path, 'data', 'lockouts_testing.json')
        for path in (test_limits, test_lockouts):
            if os.path.exists(path):
                os.remove(path)
        rate_limiter = RateLimiter(base_path, limits_file=test_limits, lockouts_file=test_lockouts)
    else:
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

    # Start cleanup thread only in real runtime, never during automated tests.
    if not app.config.get('TESTING') and not _is_pytest_running():
        cleanup_thread = threading.Thread(target=cleanup_rate_limits, daemon=True)
        cleanup_thread.start()

    if not _is_pytest_running():
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
    app.register_blueprint(admin_help_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_analytics_bp)
    app.register_blueprint(admin_notifications_bp)
    app.register_blueprint(admin_seo_bp)
    app.register_blueprint(admin_api_docs_bp)
    from lib.routes.admin.manage.backup import backup_bp
    app.register_blueprint(backup_bp)
    app.register_blueprint(youtube_bp)
    app.register_blueprint(modmail_bp)

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

    # Admin help page is now registered via admin_help_bp blueprint

    # Load plugins (keeping existing logic)
    load_plugins(app)

    # Make plugin helpers available in templates
    @app.context_processor
    def inject_plugin_check():
        from flask import session
        from lib.data.notification_manager import NotificationManager
        from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

        # Get notification count for admin users
        notification_count = 0
        try:
            # Check if user is logged in and is admin
            if 'user' in session:
                base_path = os.path.abspath(os.path.dirname(__file__))
                auth = IdentitasAuthManager(base_path)
                user_role = auth.get_user_role(session['user'])
                if user_role == 'administrator':
                    notification_manager = NotificationManager(base_path)
                    notification_count = notification_manager.get_unread_count()
        except Exception as e:
            # Silently fail if notifications aren't available or there's an error
            pass

        return dict(
            is_plugin_loaded=is_plugin_loaded,
            is_plugin_available=is_plugin_available,
            notification_unread_count=notification_count
        )

    @app.context_processor
    def inject_build_info():
        # Expose generated build info to templates (if available)
        try:
            build_info_path = os.path.join(os.path.dirname(__file__), "data", "build_info.json")
            if os.path.exists(build_info_path):
                with open(build_info_path, "r", encoding="utf-8") as f:
                    import json as _json
                    info = _json.load(f)
                    return dict(build_info=info)
        except Exception:
            pass
        return dict(build_info=None)

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

    @app.before_request
    def check_rate_limits():
        """Deny clients that exceed the configured request limit using a single source IP."""
        from flask import request, abort

        ip = get_client_ip()
        if request.path.startswith('/static') or request.path.startswith('/uploads'):
            max_requests = 1000
        elif request.path.startswith('/admin'):
            max_requests = 100
        else:
            max_requests = 300

        # Use the same default limit threshold as the app-level limiter.
        if rate_limiter.is_rate_limited(f"ip_{ip}"):
            print(f"Rate limit exceeded for IP: {ip}, path: {request.path}")
            abort(429)

    @app.errorhandler(429)
    def rate_limit_error(error):
        return render_template('error.html', error_code=429, error_message='Too many requests. Please try again later.'), 429

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('error.html', error_code=403, error_message='Access denied.'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error.html', error_code=404, error_message='Page not found.'), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template('error.html', error_code=500, error_message='Internal server error.'), 500

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
from lib.routes.admin.manage.notifications.index import admin_notifications_bp
from lib.routes.admin.manage.seo.index import admin_seo_bp
from lib.routes.admin.manage.api_docs.index import admin_api_docs_bp
from lib.routes.admin.help import admin_help_bp
from lib.routes.root.auth import auth_bp
from lib.routes.data.youtube import youtube_bp
from lib.routes.modmail import modmail_bp
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
import os
from datetime import datetime
import yaml

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use environment variables only

# Initialize Flask app
app = Flask(__name__)

# Configure UTF-8 encoding for all responses
app.config['JSON_AS_ASCII'] = False
app.config['DEFAULT_LANG'] = 'de'
app.jinja_env.enable_async = False
import sys
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure and initialize translator
app.config['DEFAULT_LANG'] = 'de'
app.config['DEFAULT_MESSAGE'] = 'Translation Error'
app.config['TRANSLATIONS_PATH'] = 'translations'
from flask_translator import Translator
class UTF8Translator(Translator):
    def _get_file_data(self):
        language = self._language or app.config.get('DEFAULT_LANG', 'en')
        translation_file = os.path.join(
            app.root_path,
            app.config['TRANSLATIONS_PATH'],
            f'messages.{language}.yaml'
        )

        with open(translation_file, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        return data

    def translate(self, key: str, **kwargs):
        if self._language is None:
            self._language = app.config.get('DEFAULT_LANG', 'en')
        return super().translate(key, **kwargs)

t = UTF8Translator()
t.init_app(app)
t._language = app.config.get('DEFAULT_LANG', 'en')

@app.context_processor
def inject_translator():
    from flask import request
    import json
    
    # Try to get language preference from settings
    lang = app.config.get('DEFAULT_LANG', 'en')
    try:
        settings_file = os.path.join(app.root_path, 'data', 'settings.json')
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # If site_language is set to a specific language, use it
                if settings.get('site_language') and settings.get('site_language') != 'auto':
                    lang = settings.get('site_language', 'en')
                else:
                    # Extract language from Accept-Language header
                    current_lang = t._language or lang
                    lang_raw = current_lang
                    if ',' in lang_raw:
                        lang = lang_raw.split(',')[0].strip()
                    elif ';' in lang_raw:
                        lang = lang_raw.split(';')[0].strip()
                    else:
                        lang = lang_raw.strip()
                    
                    # Ensure it's a valid language code (just the base language, no country)
                    if '-' in lang:
                        lang = lang.split('-')[0]
    except Exception:
        pass

    if not lang or lang in ('None', 'none'):
        lang = app.config.get('DEFAULT_LANG', 'en')
    
    # Set the translator language to the parsed language code
    t._language = lang
    return dict(t=t.translate)

# Get base path for security configuration
base_path = os.path.abspath(os.path.dirname(__file__))

# Apply secure configuration
secure_config = SecureConfig.get_config(base_path)
app.config.update(secure_config)

# Trust X-Forwarded headers only for explicitly configured proxy IPs.
is_testing_mode = bool(
    app.config.get('TESTING')
    or os.environ.get('PYTEST_CURRENT_TEST') is not None
    or os.environ.get('CI', '').lower() == 'true'
)
trusted_proxy_ips = set() if is_testing_mode else {
    entry.strip()
    for entry in os.environ.get('TRUSTED_PROXY_IPS', '').split(',')
    if entry.strip()
}
if trusted_proxy_ips:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)
else:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=0, x_host=0, x_port=0, x_prefix=0)


def get_client_ip():
    """Return the real client IP unless a trusted proxy explicitly forwarded the request."""
    from flask import request

    remote_ip = request.remote_addr or 'unknown'
    if is_testing_mode:
        return remote_ip

    forwarded_for = request.headers.get('X-Forwarded-For', '').strip()
    if not forwarded_for:
        return remote_ip

    if remote_ip not in trusted_proxy_ips:
        return remote_ip

    candidates = [entry.strip() for entry in forwarded_for.split(',') if entry.strip()]
    return candidates[0] if candidates else remote_ip

# Initialize encryption system
init_encryption(base_path)
config_encryption = ConfigEncryption(base_path)

# Add security headers to all responses
add_security_headers(app)

# Initialize rate limiter; keep the testing state isolated from the production file-backed store.
if app.config.get('TESTING'):
    test_limits = os.path.join(base_path, 'data', 'rate_limits_testing.json')
    test_lockouts = os.path.join(base_path, 'data', 'lockouts_testing.json')
    for path in (test_limits, test_lockouts):
        if os.path.exists(path):
            os.remove(path)
    rate_limiter = RateLimiter(base_path, limits_file=test_limits, lockouts_file=test_lockouts)
else:
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

# Start cleanup thread only for real runtime, not during pytest/CI execution.
if not _is_pytest_running():
    cleanup_thread = threading.Thread(target=cleanup_rate_limits, daemon=True)
    cleanup_thread.start()

if not _is_pytest_running():
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
app.register_blueprint(admin_help_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_analytics_bp)
app.register_blueprint(admin_notifications_bp)
app.register_blueprint(admin_seo_bp)
app.register_blueprint(admin_api_docs_bp)
from lib.routes.admin.manage.backup import backup_bp
app.register_blueprint(backup_bp)
app.register_blueprint(youtube_bp)
app.register_blueprint(modmail_bp)

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
    from flask import session
    from lib.data.notification_manager import NotificationManager
    from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

    # Get notification count for admin users
    notification_count = 0
    try:
        # Check if user is logged in and is admin
        if 'user' in session:
            base_path = os.path.abspath(os.path.dirname(__file__))
            auth = IdentitasAuthManager(base_path)
            user_role = auth.get_user_role(session['user'])
            if user_role == 'administrator':
                notification_manager = NotificationManager(base_path)
                notification_count = notification_manager.get_unread_count()
    except Exception as e:
        # Silently fail if notifications aren't available or there's an error
        pass

    return dict(
        is_plugin_loaded=is_plugin_loaded,
        is_plugin_available=is_plugin_available,
        notification_unread_count=notification_count
    )

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
    """DDOS protection - rate limit by the real client IP only."""
    from flask import request, abort

    ip = get_client_ip()

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
        "ip": get_client_ip(),
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
import requests

# CRITICAL: Import license check before anything else
# This runs at module import time and blocks the app if license is invalid
import _license_check


def ensure_license_valid():
    """Legacy function for CLI compatibility.
    License is already validated at module import time via _license_check.
    """
    pass  # License already validated at import time


if __name__ == "__main__":
    # License is already validated at module import time via _license_check
    handle_cli()

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--prod", action="store_true", help="Enable production mode and secure session cookies")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL")
    parser.add_argument("--cert", type=str, help="Path to SSL certificate")
    parser.add_argument("--key", type=str, help="Path to SSL private key")
    parser.add_argument("--port", type=int, help="Port to listen on")

    args = parser.parse_args()

    # SSL aktiv?
    ssl_context = None
    if args.ssl:
        if not args.cert or not args.key:
            raise ValueError("SSL requires --cert and --key")
        ssl_context = (args.cert, args.key)

    if args.prod:
        app.config["SESSION_COOKIE_SECURE"] = True

    app.run(
        debug=args.debug,
        port=args.port,
        ssl_context=ssl_context,
        host="0.0.0.0"
    )