import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, abort
from ...netdefense.auth.provider import AuthManager
import json

auth_bp = Blueprint("auth", __name__)

# AuthManager initialisieren – korrektes Projekt-Root
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
auth = AuthManager(BASE_PATH)

@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_action():
    username = request.form.get("username")
    password = request.form.get("password")

    if not username or not password:
        return jsonify({"error": "Benutzername und Passwort erforderlich"}), 400

    if auth.verify_login(username, password):
        auth.login(username)
        return redirect(url_for("admin_posts.admin_posts_index"))

    return render_template("auth/login.html", error="Login fehlgeschlagen")


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("auth/register.html")


@auth_bp.route("/register", methods=["POST"])
def register_action():
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")

    if not username or not password or not email:
        return render_template("auth/register.html", error="Benutzername, E-Mail und Passwort erforderlich")

    if auth.verify_login(username, password):  # Check if user exists
        return render_template("auth/register.html", error="Benutzername bereits vergeben")

    ok, msg = auth.create_user(username, password, "subscriber", email)
    if ok:
        auth.login(username)
        return redirect(url_for("root.index"))
    else:
        return render_template("auth/register.html", error=msg)


@auth_bp.route("/logout", methods=["GET"])
def logout():
    auth.logout()
    return redirect(url_for("root.index"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "user" not in session:
        return redirect(url_for("auth.login_page"))
    
    error = None
    success = None
    settings = {}
    settings_file = os.path.join(BASE_PATH, "data", "settings.json")
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            settings = json.load(f)
    if settings["allow_password_change"] == False:
        abort(403, description="Passwortänderungen sind nicht erlaubt")
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not all([old_password, new_password, confirm_password]):
            error = "Alle Felder sind erforderlich"
        elif new_password != confirm_password:
            error = "Die neuen Passwörter stimmen nicht überein"
        elif len(new_password) < 6:
            error = "Das neue Passwort muss mindestens 6 Zeichen lang sein"
        elif not auth.verify_login(session["user"], old_password):
            error = "Das alte Passwort ist falsch"
        else:
            ok, msg = auth.change_password(session["user"], new_password)
            if ok:
                success = "Passwort erfolgreich geändert"
            else:
                error = msg
    
    return render_template("auth/change_password.html", error=error, success=success)