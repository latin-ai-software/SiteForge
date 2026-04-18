import os
import json
from flask import Blueprint, current_app, render_template
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
                           auth=auth)