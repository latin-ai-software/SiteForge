import os
import json
import hashlib
import secrets
from functools import wraps
from flask import session, redirect, url_for, abort
from datetime import datetime


class AuthManager:
    def __init__(self, base_path):
        self.userfile = os.path.join(base_path, "data", "users.json")
        self.base_path = base_path
        os.makedirs(os.path.dirname(self.userfile), exist_ok=True)

        if not os.path.exists(self.userfile):
            with open(self.userfile, "w", encoding="utf-8") as f:
                json.dump({}, f)
    
    def _get_encryption_manager(self):
        """Get encryption manager if available"""
        try:
            from ..security.encrypted_files import get_encryption_manager
            return get_encryption_manager()
        except:
            return None

    def _load(self):
        """Load user data with automatic decryption if encrypted"""
        encryption_mgr = self._get_encryption_manager()
        
        if encryption_mgr:
            try:
                return encryption_mgr.load_json(self.userfile)
            except Exception as e:
                print(f"Decryption failed: {e}, falling back to plain read")
                # Fallback to plain read
                pass
        
        # Plain read
        with open(self.userfile, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data):
        """Save user data with automatic encryption if enabled"""
        encryption_mgr = self._get_encryption_manager()
        
        if encryption_mgr:
            try:
                encryption_mgr.save_json(self.userfile, data)
                return
            except Exception as e:
                print(f"Encryption save failed: {e}, falling back to plain write")
                # Fallback to plain write
                pass
        
        # Plain write
        os.makedirs(os.path.dirname(self.userfile), exist_ok=True)
        with open(self.userfile, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def _hash(self, password, salt):
        return hashlib.sha256((password + salt).encode()).hexdigest()

    # -------------------------
    # Benutzerverwaltung
    # -------------------------

    def create_user(self, username, password, role="subscriber", email=""):
        users = self._load()

        if username in users:
            return False, "User exists"

        salt = secrets.token_hex(16)
        users[username] = {
            "salt": salt,
            "password": self._hash(password, salt),
            "role": role,
            "email": email,
            "created_at": str(datetime.now())
        }

        self._save(users)
        return True, "User created"

    def delete_user(self, username):
        users = self._load()

        if username not in users:
            return False, "User not found"

        del users[username]
        self._save(users)
        return True, "User deleted"

    def change_password(self, username, new_password):
        users = self._load()

        if username not in users:
            return False, "User not found"

        salt = secrets.token_hex(16)
        users[username]["salt"] = salt
        users[username]["password"] = self._hash(new_password, salt)

        self._save(users)
        return True, "Password changed"

    # -------------------------
    # Login / Logout
    # -------------------------

    def verify_login(self, username, password):
        users = self._load()

        if username not in users:
            return False

        salt = users[username]["salt"]
        hashed = self._hash(password, salt)

        return hashed == users[username]["password"]

    def login(self, username):
        session["user"] = username

    def logout(self):
        session.pop("user", None)

    def current_user(self):
        """Get the currently logged-in user from session"""
        return session.get("user")

    def get_user_role(self, username):
        users = self._load()
        return users.get(username, {}).get("role", "subscriber")

    def update_user_role(self, username, role):
        users = self._load()
        if username not in users:
            return False, "User not found"
        users[username]["role"] = role
        self._save(users)
        return True, "Role updated"

    def update_user_git_access(self, username, git_access):
        users = self._load()
        if username not in users:
            return False, "User not found"
        users[username]["git_access"] = bool(git_access)
        self._save(users)
        return True, "Git access updated"

    def has_git_access(self, username):
        if self.get_user_role(username) == "administrator":
            return True
        users = self._load()
        return bool(users.get(username, {}).get("git_access", False))

    def get_user(self, username):
        """Get full user object including email and role"""
        users = self._load()
        if username not in users:
            return None
        return {
            "username": username,
            "role": users[username].get("role", "subscriber"),
            "email": users[username].get("email", ""),
            "created_at": users[username].get("created_at", "")
        }

    def update_email(self, username, email):
        """Update user's email address"""
        users = self._load()
        if username not in users:
            return False, "User not found"
        users[username]["email"] = email
        self._save(users)
        return True, "Email updated"

    def get_email(self, username):
        """Get user's email address"""
        users = self._load()
        return users.get(username, {}).get("email", "")

    # -------------------------
    # Route‑Schutz
    # -------------------------

    def require_login(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("auth.login_page"))
            return f(*args, **kwargs)
        return wrapper

    def require_admin(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("auth.login_page"))
            user_role = self.get_user_role(user)
            if user_role != "administrator":
                abort(403, description="Administratorzugriff erforderlich")
            return f(*args, **kwargs)
        return wrapper

    def require_role(self, required_role):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                user = session.get("user")
                if not user:
                    return redirect(url_for("auth.login_page"))
                user_role = self.get_user_role(user)
                role_hierarchy = {
                    "administrator": 5,
                    "editor": 4,
                    "author": 3,
                    "contributor": 2,
                    "subscriber": 1
                }
                if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 0):
                    abort(403)
                return f(*args, **kwargs)
            return wrapper
        return decorator