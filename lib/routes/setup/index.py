"""Setup/Configuration route for first-time initialization"""
import os
import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

setup_bp = Blueprint('setup', __name__, url_prefix='/setup')

def get_settings_file(base_path):
    """Get the path to settings.json"""
    return os.path.join(base_path, 'data', 'settings.json')

def get_data_dir(base_path):
    """Get the data directory"""
    return os.path.join(base_path, 'data')

def get_default_settings():
    """Get default settings structure with all required keys"""
    return {
        'setup_completed': False,
        'site_title': 'My Awesome Site',
        'site_description': 'Welcome to my site',
        'posts_per_page': 10,
        'allow_registration': True,
        'require_comment_approval': True,
        'allow_robot_indexing': False,
        'facebook_page': '',
        'robot_user_agents': '*',
        'require_cookie_consent': True,
        'cookie_consent_message': '<p>Please accept cookies to use this site.</p>',
        'enable_analytics': False,
        'analytics_provider': 'builtin',
        'analytics_tracking_id': '',
        'analytics_period_days': 30,
        'embed_favicon_in_html': True,
        'imprint_enabled': False,
        'allow_password_change': False,
        'domain': 'http://localhost',
        'header_background_enabled': False,
        'enabled_plugins': {},
        'newsletter_enabled': False,
        'newsletter_sender_email': '',
        'ses_smtp_host': '',
        'ses_smtp_port': 587,
        'ses_smtp_username': '',
        'ses_smtp_password': '',
        'show_social_links': False,
        'twitter_handle': ''
    }

def load_settings(base_path):
    """Load settings with defaults merged in"""
    defaults = get_default_settings()
    settings_file = get_settings_file(base_path)
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                # Merge user settings over defaults
                defaults.update(user_settings)
                return defaults
        except (json.JSONDecodeError, IOError) as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not load settings: {e}")
            return defaults
    
    return defaults

def initialize_data_files(base_path):
    """Initialize all required data files with proper structure"""
    data_dir = get_data_dir(base_path)
    os.makedirs(data_dir, exist_ok=True)
    
    # Define all required data files with their default structures
    required_files = {
        'posts_metadata.json': {},
        'comments.json': {},
        'analytics.json': {'visitors': []},
        'git_prs.json': {},
        'git_repos.json': {},
        'index_text.json': {},
        'index_texts.json': {},
        'lockouts.json': {},
        'media_usage.json': {},
        'rate_limits.json': {},
    }
    
    # Create required JSON files
    for filename, default_structure in required_files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_structure, f, indent=4)
            except Exception as e:
                print(f"Warning: Could not create {filename}: {e}")
    
    # Create required directories
    required_dirs = [
        'posts',
        'git_repos',
        'uploads',
    ]
    
    for dirname in required_dirs:
        dirpath = os.path.join(data_dir, dirname)
        os.makedirs(dirpath, exist_ok=True)
    
    # Create active_theme.txt if it doesn't exist
    theme_file = os.path.join(data_dir, 'active_theme.txt')
    if not os.path.exists(theme_file):
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                f.write('default')
        except Exception as e:
            print(f"Warning: Could not create active_theme.txt: {e}")

def is_setup_completed(base_path):
    """Check if setup has been completed"""
    settings_file = get_settings_file(base_path)
    if not os.path.exists(settings_file):
        return False
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings.get('setup_completed', False)
    except:
        return False

def mark_setup_completed(base_path):
    """Mark setup as completed"""
    settings_file = get_settings_file(base_path)
    os.makedirs(os.path.dirname(settings_file), exist_ok=True)
    
    settings = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except:
            settings = {}
    
    settings['setup_completed'] = True
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

@setup_bp.route('/', methods=['GET'])
def setup_page():
    """Display setup configuration page"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # If setup is already completed, redirect to home
    if is_setup_completed(base_path):
        return redirect(url_for('root.index'))
    
    return render_template('setup/index.html')

@setup_bp.route('/configure', methods=['POST'])
def configure():
    """Process setup configuration"""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    
    # If setup is already completed, deny access
    if is_setup_completed(base_path):
        return jsonify({'success': False, 'message': 'Setup already completed'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('site_title'):
            return jsonify({'success': False, 'message': 'Site title is required'}), 400
        
        if not data.get('admin_username'):
            return jsonify({'success': False, 'message': 'Admin username is required'}), 400
        
        if not data.get('admin_password'):
            return jsonify({'success': False, 'message': 'Admin password is required'}), 400
        
        if not data.get('admin_password_confirm'):
            return jsonify({'success': False, 'message': 'Password confirmation is required'}), 400
        
        if data.get('admin_password') != data.get('admin_password_confirm'):
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if len(data.get('admin_password', '')) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'}), 400
        
        # Start with default settings
        settings = get_default_settings()
        
        # Update with user-provided values
        settings['site_title'] = data.get('site_title', 'My Site')
        settings['site_description'] = data.get('site_description', '')
        settings['posts_per_page'] = int(data.get('posts_per_page', 10))
        settings['allow_registration'] = data.get('allow_registration', True)
        settings['require_comment_approval'] = data.get('require_comment_approval', True)
        settings['allow_robot_indexing'] = data.get('allow_robot_indexing', False)
        settings['require_cookie_consent'] = data.get('require_cookie_consent', True)
        settings['enable_analytics'] = data.get('enable_analytics', False)
        settings['newsletter_enabled'] = data.get('newsletter_enabled', False)
        settings['domain'] = data.get('domain', 'http://localhost')

        # Initialize all required data files and directories
        initialize_data_files(base_path)
        
        # Save settings with all defaults
        settings_file = get_settings_file(base_path)
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)
        settings['setup_completed'] = True
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
        
        # Create admin user
        auth_manager = IdentitasAuthManager(base_path)
        success, message = auth_manager.create_user(
            data.get('admin_username'),
            data.get('admin_password'),
            'administrator'
        )
        
        if not success:
            return jsonify({'success': False, 'message': f'Admin user creation failed: {message}'}), 400
        
        return jsonify({
            'success': True, 
            'message': 'Setup completed successfully',
            'redirect': url_for('root.index')
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Setup failed: {str(e)}'}), 500
