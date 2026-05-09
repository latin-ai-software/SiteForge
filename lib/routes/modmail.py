# lib/routes/modmail.py

import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from lib.data.modmail_manager import ModmailManager

modmail_bp = Blueprint("modmail", __name__, url_prefix="/modmail")

# Initialize managers
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
auth = IdentitasAuthManager(BASE_PATH)
modmail_manager = ModmailManager(BASE_PATH)

@modmail_bp.route("/", methods=["GET"])
@auth.require_login
def modmail_index():
    """User modmail interface"""
    if not modmail_manager.is_modmail_enabled():
        flash("Modmail is currently disabled", "error")
        return redirect(url_for("root.index"))

    user_id = auth._get_user_id(session.get("user"))
    conversations = modmail_manager.get_conversations_for_user(user_id)
    subjects = modmail_manager.get_subjects()

    return render_template("modmail/index.html",
                         conversations=conversations,
                         subjects=subjects)

@modmail_bp.route("/create", methods=["POST"])
@auth.require_login
def create_conversation():
    """Create a new modmail conversation"""
    if not modmail_manager.is_modmail_enabled():
        return jsonify({"error": "Modmail is disabled"}), 400

    user_id = auth._get_user_id(session.get("user"))
    subject_id = request.form.get("subject_id", type=int)
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    password = request.form.get("password", "")

    if not all([subject_id, title, message, password]):
        return jsonify({"error": "All fields are required"}), 400

    # Verify password
    if not auth.verify_login(session.get("user"), password):
        return jsonify({"error": "Invalid password"}), 400

    success, result = modmail_manager.create_conversation(
        user_id, subject_id, title, message, password
    )

    if success:
        return jsonify({"success": True, "message": "Conversation created successfully"})
    else:
        return jsonify({"error": result}), 400

@modmail_bp.route("/conversation/<int:conversation_id>", methods=["GET", "POST"])
@auth.require_login
def view_conversation(conversation_id):
    """View and reply to a conversation"""
    if not modmail_manager.is_modmail_enabled():
        flash("Modmail is currently disabled", "error")
        return redirect(url_for("root.index"))

    user_id = auth._get_user_id(session.get("user"))
    user_role = auth.get_user_role(session.get("user"))
    is_admin = user_role == "administrator"

    # Get conversation and verify access
    from lib.data.modmail_models import ModmailConversation
    from sqlalchemy.orm import Session as DBSession

    with DBSession(auth.engine) as db_session:
        conversation = db_session.query(ModmailConversation).filter_by(id=conversation_id).first()
        if not conversation:
            flash("Conversation not found", "error")
            return redirect(url_for("modmail.modmail_index"))

        # Check if user has access to this conversation
        if not is_admin and conversation.user_id != user_id:
            flash("Access denied", "error")
            return redirect(url_for("modmail.modmail_index"))

        if request.method == "POST":
            # Handle reply
            message = request.form.get("message", "").strip()
            password = request.form.get("password", "")

            if not message or not password:
                flash("Message and password are required", "error")
            elif not auth.verify_login(session.get("user"), password):
                flash("Invalid password", "error")
            else:
                success, result = modmail_manager.add_message(
                    conversation_id, user_id, message, password, is_admin
                )
                if success:
                    flash("Message sent successfully", "success")
                else:
                    flash(f"Error sending message: {result}", "error")

            return redirect(url_for("modmail.view_conversation", conversation_id=conversation_id))

        # GET request - show conversation
        password = request.args.get("password", "")
        if not password:
            return render_template("modmail/view.html",
                                 conversation=conversation,
                                 messages=[],
                                 needs_password=True)

        # Try to decrypt messages
        try:
            messages = modmail_manager.get_conversation_messages(conversation_id, password)
            return render_template("modmail/view.html",
                                 conversation=conversation,
                                 messages=messages,
                                 needs_password=False)
        except:
            flash("Failed to decrypt messages - check your password", "error")
            return render_template("modmail/view.html",
                                 conversation=conversation,
                                 messages=[],
                                 needs_password=True)

# Admin routes
@modmail_bp.route("/admin", methods=["GET"])
@auth.require_admin
def admin_modmail():
    """Admin modmail interface"""
    conversations = modmail_manager.get_conversations_for_admin()
    subjects = modmail_manager.get_subjects()

    return render_template("admin/modmail/index.html",
                         conversations=conversations,
                         subjects=subjects,
                         modmail_enabled=modmail_manager.is_modmail_enabled())

@modmail_bp.route("/admin/settings", methods=["POST"])
@auth.require_admin
def admin_settings():
    """Toggle modmail enabled/disabled"""
    enabled = request.form.get("enabled") == "on"
    if modmail_manager.set_modmail_enabled(enabled):
        flash("Modmail settings updated", "success")
    else:
        flash("Failed to update settings", "error")

    return redirect(url_for("modmail.admin_modmail"))

@modmail_bp.route("/admin/subjects/create", methods=["POST"])
@auth.require_admin
def create_subject():
    """Create a new modmail subject"""
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Subject name is required", "error")
    else:
        success, message = modmail_manager.create_subject(name, description)
        if success:
            flash("Subject created successfully", "success")
        else:
            flash(message, "error")

    return redirect(url_for("modmail.admin_modmail"))

@modmail_bp.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
@auth.require_admin
def delete_subject(subject_id):
    """Delete a modmail subject"""
    success, message = modmail_manager.delete_subject(subject_id)
    if success:
        flash("Subject deleted", "success")
    else:
        flash(message, "error")

    return redirect(url_for("modmail.admin_modmail"))

@modmail_bp.route("/admin/conversation/<int:conversation_id>/close", methods=["POST"])
@auth.require_admin
def close_conversation(conversation_id):
    """Close a modmail conversation"""
    success, message = modmail_manager.close_conversation(conversation_id)
    if success:
        flash("Conversation closed", "success")
    else:
        flash(message, "error")

    return redirect(url_for("modmail.admin_modmail"))