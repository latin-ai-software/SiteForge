import os
from flask import Blueprint, render_template, request, jsonify, abort, redirect,url_for
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
        return redirect(url_for("admin_users.admin_users_index"))
    else:
        return jsonify({"error": msg}), 400

# POST: Benutzerpasswort ändern (Admin)
@admin_users_bp.route("/change-password/<username>", methods=["POST"])
@auth.require_admin
def change_user_password(username):
    new_password = request.form.get("password")
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Passwort muss mindestens 6 Zeichen lang sein"}), 400

    success, msg = auth.change_password(username, new_password)
    if success:
        return redirect(url_for("admin_users.admin_users_index"))
    else:
        return jsonify({"error": msg}), 400

# POST: Git-Zugriff aktualisieren
@admin_users_bp.route("/update-git-access/<username>", methods=["POST"])
@auth.require_admin
def update_user_git_access(username):
    git_access = request.form.get("git_access") == "on"
    success, msg = user_manager.update_user_git_access(username, git_access)
    if success:
        return redirect(url_for("admin_users.admin_users_index"))
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