import os
from flask import Blueprint, render_template, request, jsonify, current_app, abort, session
from .....netdefense.auth.provider import AuthManager
from .....data.post_manager import PostManager
from .....data.file_manager import FileManager

admin_posts_bp = Blueprint("admin_posts", __name__, url_prefix="/admin/posts")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)
post_manager = PostManager(BASE_PATH)
file_manager = FileManager(BASE_PATH)

# Hilfsfunktion: Pfad zu Posts
def posts_dir():
    return os.path.join(current_app.root_path, "data", "posts")


# CREATE: Neuen Beitrag erstellen
@admin_posts_bp.route("/create", methods=["GET"])
@auth.require_role("author")
def create_post_form():
    return render_template("admin/posts/create.html")


# POST: Neuen Beitrag speichern
@admin_posts_bp.route("/create", methods=["POST"])
@auth.require_role("author")
def create_post():
    title = request.form.get("title")
    content = request.form.get("content")
    categories = [cat.strip() for cat in request.form.get("categories", "").split(",") if cat.strip()]
    tags = [tag.strip() for tag in request.form.get("tags", "").split(",") if tag.strip()]

    if not title or not content:
        return jsonify({"error": "title und content erforderlich"}), 400

    # Handle file uploads
    attachments = []
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file and file.filename:
                success, result, file_info = file_manager.save_file(file)
                if success:
                    attachments.append({
                        'original_name': file_info['original_name'],
                        'filename': file_info['filename'],
                        'size': file_info['size'],
                        'mime_type': file_info['mime_type']
                    })
                else:
                    # Continue with other files but log the error
                    print(f"Failed to upload {file.filename}: {result}")

    author = auth.current_user() or session.get("user")
    post_id = post_manager.create_post(title, content, author, categories=categories, tags=tags, attachments=attachments)

    return jsonify({"status": "ok", "post_id": post_id})


# LISTE: Alle Beiträge anzeigen (HTML)
@admin_posts_bp.route("/", methods=["GET"])
@auth.require_role("author")
def admin_posts_index():
    posts = post_manager.get_posts(status=None)  # Get all posts regardless of status

    return render_template("admin/posts/index.html", posts=posts)


# GET: Beitrag bearbeiten
@admin_posts_bp.route("/edit/<post_id>", methods=["GET"])
@auth.require_role("author")
def edit_post(post_id):
    post = post_manager.get_post(post_id)

    if not post:
        abort(404)

    # Check if user can edit this post
    current_user = auth.current_user()
    user_role = auth.get_user_role(current_user)
    if user_role not in ["administrator", "editor"] and post["author"] != current_user:
        abort(403)

    return render_template("admin/posts/edit.html", post=post)


# POST: Beitrag speichern (Update)
@admin_posts_bp.route("/edit/<post_id>", methods=["POST"])
@auth.require_role("author")
def save_post(post_id):
    title = request.form.get("title")
    content = request.form.get("content")
    categories = [cat.strip() for cat in request.form.get("categories", "").split(",") if cat.strip()]
    tags = [tag.strip() for tag in request.form.get("tags", "").split(",") if tag.strip()]

    if not title or not content:
        return jsonify({"error": "title und content erforderlich"}), 400

    # Check permissions
    post = post_manager.get_post(post_id)
    if not post:
        abort(404)

    current_user = auth.current_user()
    user_role = auth.get_user_role(current_user)
    if user_role not in ["administrator", "editor"] and post["author"] != current_user:
        abort(403)

    # Handle file uploads
    attachments = post.get("attachments", [])  # Keep existing attachments
    if 'attachments' in request.files:
        files = request.files.getlist('attachments')
        for file in files:
            if file and file.filename:
                success, result, file_info = file_manager.save_file(file)
                if success:
                    attachments.append({
                        'original_name': file_info['original_name'],
                        'filename': file_info['filename'],
                        'size': file_info['size'],
                        'mime_type': file_info['mime_type']
                    })
                else:
                    # Continue with other files but log the error
                    print(f"Failed to upload {file.filename}: {result}")

    success = post_manager.update_post(post_id, title=title, content=content, categories=categories, tags=tags, attachments=attachments)

    if success:
        return jsonify({"status": "ok", "updated": post_id})
    else:
        return jsonify({"error": "Post not found"}), 404


# DELETE: Beitrag löschen
@admin_posts_bp.route("/delete/<post_id>", methods=["POST"])
@auth.require_role("author")
def delete_post(post_id):
    # Check permissions
    post = post_manager.get_post(post_id)
    if not post:
        abort(404)

    current_user = auth.current_user()
    user_role = auth.get_user_role(current_user)
    if user_role not in ["administrator", "editor"] and post["author"] != current_user:
        abort(403)

    success = post_manager.delete_post(post_id)

    if success:
        return jsonify({"status": "deleted", "post_id": post_id})
    else:
        return jsonify({"error": "Post not found"}), 404
