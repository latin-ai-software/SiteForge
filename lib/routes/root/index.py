import os
import json
from flask import Blueprint, current_app, session, render_template, request
from ...data.post_manager import PostManager
from ...netdefense.auth.provider import AuthManager

root_bp = Blueprint("root", __name__)

# PostManager initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
post_manager = PostManager(BASE_PATH)
auth = AuthManager(BASE_PATH)

@root_bp.route("/", methods=["GET"])
def index():
    posts = post_manager.get_posts(limit=10)
    categories = post_manager.get_all_categories()

    # Load settings
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    # Aktives Stylesheet laden
    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    return render_template("root/index.html",
                           posts=posts,
                           categories=categories,
                           settings=settings,
                           active_theme=active_theme,
                           auth=auth,
                           show_logo=settings["embed_favicon_in_html"])
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

    # Load settings
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

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
                           show_logo=settings["embed_favicon_in_html"],
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