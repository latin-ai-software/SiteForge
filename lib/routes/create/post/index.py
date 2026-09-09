import os
from flask import Blueprint, request, jsonify, render_template, current_app, abort, redirect, url_for, make_response, session
from lib.netdefense.check import MalwareChecker
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from ....data.post_manager import PostManager
from ....data.comment_manager import CommentManager
import json

post_create_bp = Blueprint("post_create", __name__)
security = MalwareChecker()

# AuthManager initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
auth = IdentitasAuthManager(BASE_PATH)
post_manager = PostManager(BASE_PATH)
comment_manager = CommentManager(BASE_PATH)

# GET: Formular anzeigen
@post_create_bp.route("/create/post", methods=["GET"])
@auth.require_login
def create_post_form():
    return render_template("create/post/index.html")


# POST: Beitrag speichern
@post_create_bp.route("/create/post", methods=["POST"])
@auth.require_login
def create_post():
    title = request.form.get("title")
    content = request.form.get("content")

    if not title or not content:
        return jsonify({"error": "title und content erforderlich"}), 400

    # Malware-Check
    result = security.check_text(content)

    if security.is_suspicious(content):
        return jsonify({
            "error": "Tried to upload Malware!",
            "details": result
        }), 400

    author = auth.current_user()
    post_id = post_manager.create_post(title, content, author)

    return jsonify({"status": "ok", "post_id": post_id})
# GET: Post ausliefern
@post_create_bp.route("/post/<slug>", methods=["GET"])
def get_post(slug):
    post = post_manager.get_post(slug)

    if not post:
        abort(404)

    if post.get("status", "publish") != "publish":
        current_user = auth.current_user()
        if not current_user:
            abort(404)
        user_role = auth.get_user_role(current_user)
        if user_role not in ["administrator", "editor", "author"]:
            abort(404)

    # Load comments
    try:
        top_level_comments, replies = comment_manager.get_comments(post["id"])
    except (TypeError, ValueError):
        top_level_comments, replies = [], {}

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

    comments_allowed = post.get("allow_comments", True)

    return render_template("post/view.html",
                           post=post,
                           top_level_comments=top_level_comments,
                           replies=replies,
                           active_theme=active_theme,
                           settings=settings,
                           auth=auth,
                           comments_allowed=comments_allowed)

# POST: Kommentar hinzufügen
@post_create_bp.route("/post/<slug>/comment", methods=["POST"])
@auth.require_login
def add_comment(slug):
    post = post_manager.get_post(slug)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    author = auth.current_user() or session.get("user")
    content = request.form.get("content")
    parent_id = request.form.get("parent_id")

    if not author:
        return jsonify({"error": "Login required to post comments"}), 403
    if not content:
        return jsonify({"error": "Content required"}), 400

    # Security check for content
    result = security.check_text(content)
    if security.is_suspicious(content):
        return jsonify({
            "error": "Comment contains suspicious content!",
            "details": result
        }), 400

    # Add comment
    comment_id = comment_manager.add_comment(post["id"], author, content, parent_id)

    return jsonify({"status": "ok", "comment_id": comment_id})

# POST: Umfrage abstimmen
@post_create_bp.route("/post/<slug>/vote", methods=["POST"])
@auth.require_login
def vote_post_survey(slug):
    post = post_manager.get_post(slug)
    if not post:
        return jsonify({"error": "Post nicht gefunden"}), 404

    if not post.get("survey"):
        return jsonify({"error": "Keine Umfrage für diesen Beitrag vorhanden"}), 400

    choice = request.form.get("survey_choice")
    if not choice:
        return jsonify({"error": "Bitte wähle eine Option aus."}), 400

    user = auth.current_user()
    success, message = post_manager.vote_survey(post["id"], user, choice)
    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"status": "ok", "message": message})

# LIST: Alle Posts als JSON ausgeben
@post_create_bp.route("/posts/list", methods=["GET"])
def list_posts():
    base_path = os.path.join(current_app.root_path, "data", "posts")

    if not os.path.exists(base_path):
        return jsonify({"posts": []})

    posts = []
    for filename in os.listdir(base_path):
        if filename.endswith(".html"):
            name = filename[:-5]  # ".html" entfernen
            posts.append({
                "name": name,
                "url": f"/post/id/{name}"
            })

    return jsonify({"posts": posts})

# CATEGORY: Posts nach Kategorie
@post_create_bp.route("/category/<category>", methods=["GET"])
def posts_by_category(category):
    posts = post_manager.get_posts_by_category(category)

    # Aktives Stylesheet laden
    active_theme_path = os.path.join(current_app.root_path, "data", "active_theme.txt")
    active_theme = None
    if os.path.exists(active_theme_path):
        with open(active_theme_path, "r", encoding="utf-8") as f:
            active_theme = f.read().strip()

    return render_template("root/category.html",
                           posts=posts,
                           category=category,
                           active_theme=active_theme)

# RSS: RSS Feed
@post_create_bp.route("/feed", methods=["GET"])
def rss_feed():
    posts = post_manager.get_posts(limit=20)
    
    # Get the base URL dynamically from request or settings
    from ....newsletter import get_base_url
    base_url = get_base_url()

    rss_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    rss_content += '<rss version="2.0">\n'
    rss_content += '<channel>\n'
    rss_content += '<title>SiteForge</title>\n'
    rss_content += '<description>Latest posts from SiteForge</description>\n'
    rss_content += f'<link>{base_url}</link>\n'

    for post in posts:
        rss_content += '<item>\n'
        rss_content += f'<title>{post["title"]}</title>\n'
        rss_content += f'<description>{post["content"][:200]}...</description>\n'
        rss_content += f'<link>{base_url}/post/{post["slug"]}</link>\n'
        rss_content += f'<guid>{base_url}/post/{post["slug"]}</guid>\n'
        rss_content += f'<pubDate>{post["created_at"]}</pubDate>\n'
        rss_content += '</item>\n'

    rss_content += '</channel>\n'
    rss_content += '</rss>'

    response = make_response(rss_content)
    response.headers['Content-Type'] = 'application/rss+xml'
    return response