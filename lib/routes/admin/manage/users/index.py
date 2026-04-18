import os
from flask import Blueprint, render_template, request, jsonify, abort
from .....netdefense.auth.provider import AuthManager
from .....data.user_manager import UserManager

admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin/users")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = AuthManager(BASE_PATH)
user_manager = UserManager(BASE_PATH)

# LISTE: Alle Benutzer anzeigen
@admin_users_bp.route("/", methods=["GET"])
@auth.require_admin
def admin_users_index():
    users = user_manager.get_all_users()
    return render_template("admin/users/index.html", users=users)

# POST: Benutzerrolle aktualisieren
@admin_users_bp.route("/update-role/<username>", methods=["POST"])
@auth.require_admin
def update_user_role(username):
    role = request.form.get("role")
    if not role:
        return jsonify({"error": "role erforderlich"}), 400

    success, msg = user_manager.update_user_role(username, role)
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": msg}), 400

# POST: Benutzer löschen
@admin_users_bp.route("/delete/<username>", methods=["POST"])
@auth.require_admin
def delete_user(username):
    # Don't allow deleting self
    current_user = auth.current_user()
    if username == current_user:
        return jsonify({"error": "Cannot delete yourself"}), 400

    success, msg = user_manager.delete_user(username)
    if success:
        return jsonify({"status": "deleted"})
    else:
        return jsonify({"error": msg}), 400