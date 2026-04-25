import os
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, abort
from ...netdefense.auth.provider import AuthManager
from ...security import RateLimiter, InputValidator
import json

auth_bp = Blueprint("auth", __name__)

# AuthManager initialisieren – korrektes Projekt-Root
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
auth = AuthManager(BASE_PATH)
rate_limiter = RateLimiter(BASE_PATH)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("auth/login.html")


@auth_bp.route("/login", methods=["POST"])
def login_action():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    
    # Input validation
    if not username or not password:
        return render_template("auth/login.html", error="Username and password required"), 400
    
    if not InputValidator.validate_username(username):
        return render_template("auth/login.html", error="Invalid username format"), 400
    
    # Check account lockout
    is_locked, lockout_msg = rate_limiter.check_login_attempt(username)
    if is_locked:
        return render_template("auth/login.html", error=lockout_msg), 429
    
    # Rate limit login attempts by IP
    client_ip = request.remote_addr
    if rate_limiter.is_rate_limited(f"login_{client_ip}"):
        return render_template("auth/login.html", error="Too many login attempts. Please try again later."), 429
    
    if auth.verify_login(username, password):
        rate_limiter.reset_login_attempts(username)
        auth.login(username)
        session.permanent = True
        return redirect(url_for("admin_posts.admin_posts_index"))
    else:
        # Record failed login attempt
        rate_limiter.record_failed_login(username, max_attempts=5, lockout_duration=300)
        return render_template("auth/login.html", error="Login failed"), 401


@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("auth/register.html")


@auth_bp.route("/register", methods=["POST"])
def register_action():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    email = request.form.get("email", "").strip()
    
    # Input validation
    if not all([username, password, email]):
        return render_template("auth/register.html", error="Username, email and password required"), 400
    
    if not InputValidator.validate_username(username):
        return render_template("auth/register.html", error="Username must be 3-32 alphanumeric characters"), 400
    
    if not InputValidator.validate_email(email):
        return render_template("auth/register.html", error="Invalid email format"), 400
    
    is_strong, strength_msg = InputValidator.validate_password(password)
    if not is_strong:
        return render_template("auth/register.html", error=strength_msg), 400
    
    # Rate limit registration by IP
    client_ip = request.remote_addr
    if rate_limiter.is_rate_limited(f"register_{client_ip}"):
        return render_template("auth/register.html", error="Too many registration attempts. Please try again later."), 429
    
    if auth.verify_login(username, password):  # Check if user exists
        return render_template("auth/register.html", error="Username already taken"), 400

    ok, msg = auth.create_user(username, password, "subscriber", email)
    if ok:
        auth.login(username)
        session.permanent = True
        return redirect(url_for("root.index"))
    else:
        return render_template("auth/register.html", error=msg), 400


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
    if settings.get("allow_password_change") == False:
        abort(403, description="Password changes are not allowed")
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not all([old_password, new_password, confirm_password]):
            error = "All fields are required"
        elif new_password != confirm_password:
            error = "New passwords do not match"
        elif not auth.verify_login(session["user"], old_password):
            error = "Old password is incorrect"
        else:
            is_strong, strength_msg = InputValidator.validate_password(new_password)
            if not is_strong:
                error = strength_msg
            else:
                ok, msg = auth.change_password(session["user"], new_password)
                if ok:
                    success = "Password changed successfully"
                else:
                    error = msg
    
    return render_template("auth/change_password.html", error=error, success=success)