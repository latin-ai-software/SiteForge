import os
import json
from flask import Blueprint, current_app, session, render_template, request, abort, redirect, url_for
from ...data.post_manager import PostManager
from ...data.comment_manager import CommentManager
from ...netdefense.auth.identitas_auth import IdentitasAuthManager
from lib.newsletter import subscribe_email

root_bp = Blueprint("root", __name__)

# PostManager initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
post_manager = PostManager(BASE_PATH)
comment_manager = CommentManager(BASE_PATH)
auth = IdentitasAuthManager(BASE_PATH)

def get_index_text():
    """Load active custom index page text from data file"""
    index_text_path = os.path.join(current_app.root_path, "data", "index_texts.json")
    if os.path.exists(index_text_path):
        try:
            with open(index_text_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                texts = data.get("texts", [])
                active_text = next((t for t in texts if t.get("active")), None)
                return active_text.get("content", "") if active_text else ""
        except:
            return ""
    return ""

def get_all_index_texts():
    """Load all custom index page texts from data file"""
    index_text_path = os.path.join(current_app.root_path, "data", "index_texts.json")
    if os.path.exists(index_text_path):
        try:
            with open(index_text_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("texts", [])
        except:
            return []
    return []

@root_bp.route("/", methods=["GET"])
def index():
    posts = post_manager.get_posts(limit=10)
    categories = post_manager.get_all_categories()

    # Load settings with safe defaults
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.warning(f"Could not load settings.json: {e}")
            settings = {}
    
    # Ensure all required settings keys exist with defaults
    settings.setdefault('embed_favicon_in_html', True)
    settings.setdefault('site_title', 'My Site')
    settings.setdefault('site_description', '')
    settings.setdefault('site_keywords', '')
    settings.setdefault('require_cookie_consent', True)
    settings.setdefault('enable_analytics', False)
    settings.setdefault('youtube_channel_id', '')
    settings.setdefault('slideshow_enabled', False)
    settings.setdefault('slideshow_interval', 10)
    settings.setdefault('slideshow_header', '')
    settings.setdefault('slideshow_subtitle', '')
    settings.setdefault('slideshow_images', [])
    settings.setdefault('slideshow_background_image', '')
    settings.setdefault('site_rating', 'G')
    settings.setdefault('age_restriction_enabled', False)

    # Aktives Stylesheet laden
    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    # Get custom index texts
    all_index_texts = get_all_index_texts()
    active_text = next((t for t in all_index_texts if t.get("active")), None)
    index_text = active_text.get("content", "") if active_text else ""
    active_text_id = active_text.get("id") if active_text else None

    return render_template("root/index.html",
                           posts=posts,
                           categories=categories,
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth,
                           show_logo=settings.get("embed_favicon_in_html", True),
                           index_text=index_text,
                           index_texts=all_index_texts,
                           active_text=active_text,
                           active_text_id=active_text_id)


@root_bp.route("/newsletter", methods=["GET", "POST"])
def newsletter_signup():
    message = None
    success = False
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        ok, message = subscribe_email(email)
        success = ok

    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    posts = post_manager.get_posts(limit=10)
    categories = post_manager.get_all_categories()

    return render_template("root/newsletter.html",
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth,
                           show_logo=settings.get("embed_favicon_in_html", False),
                           posts=posts,
                           categories=categories,
                           message=message,
                           success=success)


def get_index_text_by_id(text_id):
    all_index_texts = get_all_index_texts()
    return next((t for t in all_index_texts if t.get("id") == text_id), None)


@root_bp.route("/index-text/<text_id>", methods=["GET"])
def index_text_detail(text_id):
    text = get_index_text_by_id(text_id)
    if not text:
        abort(404)

    posts = post_manager.get_posts(limit=10)
    categories = post_manager.get_all_categories()

    # Load settings with safe defaults
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.warning(f"Could not load settings.json: {e}")
    
    settings.setdefault('embed_favicon_in_html', True)

    # Aktives Stylesheet laden
    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    top_level_comments, replies = comment_manager.get_comments(f"index_text:{text_id}")

    return render_template("root/index_text_detail.html",
                           text=text,
                           posts=posts,
                           categories=categories,
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth,
                           show_logo=settings.get("embed_favicon_in_html", True),
                           top_level_comments=top_level_comments,
                           replies=replies)


@root_bp.route("/index-text/<text_id>/comment", methods=["POST"])
def add_index_text_comment(text_id):
    if 'user' not in session:
        try:
            return redirect(url_for("auth.login_page"))
        except Exception:
            return redirect("/login")

    text = get_index_text_by_id(text_id)
    if not text:
        abort(404)

    author = session['user']
    content = request.form.get("comment", "").strip()
    parent_id = request.form.get("parent_id") or None
    if not content:
        return {"status": "error", "error": "Comment cannot be empty"}, 400

    comment_manager.add_comment(f"index_text:{text_id}", author, content, parent_id)
    return {"status": "ok"}

@root_bp.route("/profile/me", methods=["GET", "POST"])
def profile():
    # Handle email update
    if request.method == "POST" and "email" in request.form:
        if 'user' in session:
            new_email = request.form.get("email", "").strip()
            if new_email:
                auth.update_email(session['user'], new_email)

    posts = post_manager.get_posts(limit=10)
    categories = post_manager.get_all_categories()

    # Load settings with safe defaults
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            current_app.logger.warning(f"Could not load settings.json: {e}")
    
    settings.setdefault('embed_favicon_in_html', True)

    # Aktives Stylesheet laden
    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    # Get user data
    user_data = None
    activities = []
    if 'user' in session:
        user_data = auth.get_user(session['user'])
        # For activities, get user's posts
        activities = post_manager.get_posts_by_author(session['user'])[:10]  # Last 10 posts by user

    return render_template("auth/profile.html",
                           posts=posts,
                           categories=categories,
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth,
                           show_logo=settings.get("embed_favicon_in_html", True),
                           user_data=user_data,
                           activities=activities)

@root_bp.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "").strip()
    posts = []
    if query:
        posts = post_manager.search_posts(query)

    # Load settings
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    return render_template("root/search.html",
                           query=query,
                           posts=posts,
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth)