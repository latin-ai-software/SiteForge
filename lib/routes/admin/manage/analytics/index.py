import os
from flask import Blueprint, render_template, request, jsonify, current_app
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.comment_manager import CommentManager
import json
from datetime import datetime, timedelta

admin_analytics_bp = Blueprint("admin_analytics", __name__, url_prefix="/admin/analytics")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)
comment_manager = CommentManager(BASE_PATH)

# Analytics data file
ANALYTICS_FILE = os.path.join(BASE_PATH, "data", "analytics.json")

def _load_analytics():
    if not os.path.exists(ANALYTICS_FILE):
        return {"visitors": []}
    with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_analytics(data):
    os.makedirs(os.path.dirname(ANALYTICS_FILE), exist_ok=True)
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)

# ANALYTICS: Dashboard anzeigen
@admin_analytics_bp.route("/", methods=["GET"])
@auth.require_admin
def admin_analytics_index():
    # Load settings
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    # Check if analytics is enabled
    if not settings.get("enable_analytics", False):
        return render_template("admin/analytics/index.html",
                             settings=settings,
                             analytics_enabled=False,
                             visitor_count=0,
                             comments_count=0)

    # Load analytics data
    analytics = _load_analytics()

    # Calculate visitor stats
    period_days = settings.get("analytics_period_days", 30)
    cutoff_date = datetime.now() - timedelta(days=period_days)

    recent_visitors = []
    for visitor in analytics.get("visitors", []):
        visit_date = datetime.fromisoformat(visitor["timestamp"])
        if visit_date >= cutoff_date:
            recent_visitors.append(visitor)

    visitor_count = len(recent_visitors)

    # Get all comments for management
    comments_data = _load_comments_data()
    comments_count = sum(len(post_comments) for post_comments in comments_data.values())

    return render_template("admin/analytics/index.html",
                         settings=settings,
                         analytics_enabled=True,
                         visitor_count=visitor_count,
                         comments_count=comments_count,
                         recent_visitors=recent_visitors[-50:])  # Last 50 visitors

def _load_comments_data():
    comments_file = os.path.join(BASE_PATH, "data", "comments.json")
    if not os.path.exists(comments_file):
        return {}
    with open(comments_file, "r", encoding="utf-8") as f:
        return json.load(f)

# POST: Kommentar löschen
@admin_analytics_bp.route("/comments/delete", methods=["POST"])
@auth.require_admin
def delete_comment():
    post_id = request.form.get("post_id")
    comment_id = request.form.get("comment_id")

    if not post_id or not comment_id:
        return jsonify({"error": "post_id and comment_id required"}), 400

    success = comment_manager.delete_comment(post_id, comment_id)

    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Comment not found"}), 404

# GET: Kommentare für Management
@admin_analytics_bp.route("/comments", methods=["GET"])
@auth.require_admin
def manage_comments():
    comments_data = _load_comments_data()

    # Flatten comments for display
    all_comments = []
    for post_id, post_comments in comments_data.items():
        for comment in post_comments:
            comment["post_id"] = post_id
            all_comments.append(comment)

    # Sort by creation date, newest first
    all_comments.sort(key=lambda x: x["created_at"], reverse=True)

    # Load settings for template
    settings = {}
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)

    return render_template("admin/analytics/comments.html", comments=all_comments, settings=settings)