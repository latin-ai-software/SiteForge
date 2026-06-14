import os
from flask import Blueprint, render_template, request, jsonify, current_app, abort, session, redirect, url_for
from .....netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.post_manager import PostManager
from .....data.file_manager import FileManager
from .....data.media_manager import MediaManager
from lib.newsletter import send_newsletter
#lib/routes/admin/posts/index.py

admin_posts_bp = Blueprint("admin_posts", __name__, url_prefix="/admin/posts")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)
post_manager = PostManager(BASE_PATH)
file_manager = FileManager(BASE_PATH)
media_manager = MediaManager(BASE_PATH)

# Hilfsfunktion: Pfad zu Posts
def posts_dir():
    return os.path.join(current_app.root_path, "data", "posts")

# CREATE: Neuen Beitrag erstellen
@admin_posts_bp.route("/create", methods=["GET"])
@auth.require_role("author")
def create_post_form():
    git_plugin_available = 'git_repos' in current_app.blueprints
    git_repos = []
    user = auth.current_user()
    if git_plugin_available:
        # Load git repos for current user
        import json
        git_repos_file = os.path.join(BASE_PATH, "data", "git_repos.json")
        if os.path.exists(git_repos_file):
            with open(git_repos_file, "r", encoding="utf-8") as f:
                repos_data = json.load(f)
                user_repos = repos_data.get(user, {})
                git_repos = list(user_repos.keys())
    return render_template("admin/posts/create.html", git_plugin_available=git_plugin_available, git_repos=git_repos, user=user)


# POST: Neuen Beitrag speichern
@admin_posts_bp.route("/create", methods=["POST"])
@auth.require_role("author")
def create_post():
    title = request.form.get("title")
    content = request.form.get("content")
    categories = [cat.strip() for cat in request.form.get("categories", "").split(",") if cat.strip()]
    tags = [tag.strip() for tag in request.form.get("tags", "").split(",") if tag.strip()]
    git_repository = request.form.get("git_repository", "").strip()
    release_tag = request.form.get("release_tag", "").strip()
    survey_enabled = request.form.get("survey_enabled") == "on"
    survey_question = request.form.get("survey_question", "").strip()
    survey_options = [opt.strip() for opt in request.form.get("survey_options", "").splitlines() if opt.strip()]

    if not title or not content:
        return jsonify({"error": "title und content erforderlich"}), 400

    survey = None
    if survey_enabled:
        if not survey_question or len(survey_options) < 2:
            return jsonify({"error": "Umfragefrage und mindestens 2 Optionen erforderlich"}), 400
        survey = post_manager._build_survey(survey_question, survey_options)

    # Handle file uploads and existing files
    attachments = []
    
    # Add newly uploaded files
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
    
    # Add selected existing files
    existing_files = request.form.getlist('existing_files')
    for filename in existing_files:
        if filename:
            file_info = media_manager.get_file_info(filename)
            if file_info:
                attachments.append({
                    'original_name': filename,
                    'filename': filename,
                    'size': file_info['size'],
                    'mime_type': 'application/octet-stream'
                })

    author = auth.current_user() or session.get("user")
    post_id = post_manager.create_post(
        title,
        content,
        author,
        categories=categories,
        tags=tags,
        attachments=attachments,
        git_repository=git_repository,
        release_tag=release_tag,
        survey=survey
    )

    # Send newsletter update for new posts
    try:
        base_url = request.host_url.rstrip("/")
        post_url = f"{base_url}/post/{post_id}"
        summary = content.strip().replace("\n", " ")[:200]
        if len(content.strip()) > 200:
            summary += "..."
        send_newsletter(
            subject=f"SiteForge: Neuer Beitrag veröffentlicht - {title}",
            html_body=f"<p>Hallo,</p><p>es gibt einen neuen Beitrag auf <strong>{author}</strong>'s SiteForge:</p><h2>{title}</h2><p>{summary}</p><p><a href='{post_url}'>Beitrag ansehen</a></p>",
            text_body=f"Hallo,\n\nEs gibt einen neuen Beitrag auf SiteForge:\n{title}\n{post_url}\n\n{summary}"
        )
    except Exception:
        current_app.logger.exception("Newsletter konnte nach neuem Beitrag nicht gesendet werden")

    return redirect("/")


# LISTE: Alle Beiträge anzeigen (HTML)
# And how to fix jinja2.exceptions.UndefinedError: 't' is undefined in this route https://flask-translator.readthedocs.io/en/latest/#usage-in-templates
# And how exactly? Use a context processor in the main app to inject the translator's 't' function into all templates, including those rendered by Blueprints. This way, you can use {{ t("your_translation_key") }} in any template without needing to import or initialize the translator in each Blueprint separately.
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
    git_repository = request.form.get("git_repository", "").strip()
    release_tag = request.form.get("release_tag", "").strip()

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

    # Handle file uploads and existing files
    attachments = post.get("attachments", [])  # Keep existing attachments
    
    # Add newly uploaded files
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
    
    # Add selected existing files (avoid duplicates)
    existing_filenames = {att['filename'] for att in attachments}
    existing_files = request.form.getlist('existing_files')
    for filename in existing_files:
        if filename and filename not in existing_filenames:
            file_info = media_manager.get_file_info(filename)
            if file_info:
                attachments.append({
                    'original_name': filename,
                    'filename': filename,
                    'size': file_info['size'],
                    'mime_type': 'application/octet-stream'
                })

    survey_enabled = request.form.get("survey_enabled") == "on"
    survey_question = request.form.get("survey_question", "").strip()
    survey_options = [opt.strip() for opt in request.form.get("survey_options", "").splitlines() if opt.strip()]

    survey = {} if not survey_enabled else None
    if survey_enabled:
        if not survey_question or len(survey_options) < 2:
            return jsonify({"error": "Umfragefrage und mindestens 2 Optionen erforderlich"}), 400
        survey = post_manager._build_survey(survey_question, survey_options, existing_survey=post.get("survey"))

    success = post_manager.update_post(
        post_id,
        title=title,
        content=content,
        categories=categories,
        tags=tags,
        attachments=attachments,
        git_repository=git_repository,
        release_tag=release_tag,
        survey=survey
    )

    if success:
        try:
            base_url = request.host_url.rstrip("/")
            post_url = f"{base_url}/post/{post_id}"
            summary = content.strip().replace("\n", " ")[:200]
            if len(content.strip()) > 200:
                summary += "..."
            send_newsletter(
                subject=f"SiteForge: Beitrag aktualisiert - {title}",
                html_body=f"<p>Hallo,</p><p>der Beitrag " + title + " wurde aktualisiert:</p><h2>{title}</h2><p>{summary}</p><p><a href='{post_url}'>Beitrag ansehen</a></p>",
                text_body=f"Hallo,\n\nder Beitrag {title} wurde aktualisiert.\n{post_url}\n\n{summary}"
            )
        except Exception:
            current_app.logger.exception("Newsletter konnte nach Beitragsspeicherung nicht gesendet werden")
        return redirect(url_for("admin_posts.admin_posts_index"))
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
        return redirect(url_for("admin_posts.admin_posts_index"))
    else:
        return jsonify({"error": "Post not found"}), 404

@admin_posts_bp.route("/upload", methods=["POST"])
@auth.require_role("author")
def upload_post_media():
    if "file" not in request.files:
        return jsonify({"error": "Keine Datei erhalten"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Ungültiger Dateiname"}), 400

    success, result, file_info = file_manager.save_file(file)
    if not success:
        return jsonify({"error": result}), 400

    return jsonify({
        "status": "ok",
        "filename": file_info["filename"],
        "url": file_manager.get_file_url(file_info["filename"])
    }), 200
