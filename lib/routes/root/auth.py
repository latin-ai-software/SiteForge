import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ...netdefense.auth.provider import AuthManager

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
    email = request.form.get("email")  # We'll add email later

    if not username or not password:
        return render_template("auth/register.html", error="Benutzername und Passwort erforderlich")

    if auth.verify_login(username, password):  # Check if user exists
        return render_template("auth/register.html", error="Benutzername bereits vergeben")

    ok, msg = auth.create_user(username, password, "subscriber")
    if ok:
        auth.login(username)
        return redirect(url_for("root.index"))
    else:
        return render_template("auth/register.html", error=msg)


@auth_bp.route("/logout", methods=["GET"])
def logout():
    auth.logout()
    return redirect(url_for("root.index"))