"""
Identitas Authentication Wrapper

This module provides a drop-in replacement for the existing AuthManager
that uses Identitas for authentication while maintaining the same interface.

It maps the existing AuthManager methods to Identitas equivalents:
- create_user -> Identitas.register
- verify_login -> Identitas.login (returns token on success)
- login -> session-based login with token storage
- logout -> Identitas.logout + session cleanup
- change_password -> Direct password update in Identitas DB
- get_user_role -> Query role from Identitas database
- require_login -> Decorator for route protection
- require_admin -> Decorator for admin-only routes
"""

import os
import sys
from functools import wraps
from flask import session, redirect, url_for, abort, g
from datetime import datetime

# Add Identitas to path
IDENTITAS_PATH = os.path.join(os.path.dirname(__file__), "../../../Identitas")
if IDENTITAS_PATH not in sys.path:
    sys.path.insert(0, IDENTITAS_PATH)

from provider.api.auth import register as identitas_register
from provider.api.auth import login as identitas_login
from provider.api.auth import logout as identitas_logout
from provider.api.auth import validate_token as identitas_validate_token
from provider.api.rbac import create_role as rbac_create_role
from provider.api.rbac import assign_role_to_user as rbac_assign_role_to_user
from provider.api.rbac import remove_role_from_user as rbac_remove_role_from_user
from provider.api.rbac import get_user_roles as rbac_get_user_roles
from provider.api.rbac import get_role_by_name as rbac_get_role_by_name
from provider.api.rbac import user_has_right as rbac_user_has_right
from provider.api.rbac import list_roles as rbac_list_roles
from provider.backend.db_operations import create_sqlite_database
from provider.models.user import User
from sqlalchemy.orm import Session as DBSession


class IdentitasAuthManager:
    """
    Wrapper around Identitas authentication that provides the same
    interface as the original AuthManager for backward compatibility.
    """
    
    def __init__(self, base_path):
        self.base_path = base_path
        self.data_dir = os.path.join(base_path, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize Identitas database
        db_path = os.path.join(self.data_dir, "identitas.db")
        self.engine = create_sqlite_database(db_path)
        
        # Initialize default roles in RBAC
        self._init_default_roles()
        
        # Store token in session for later logout
        self._session_token_key = "identitas_token"
        self._session_user_key = "user"
    
    def _init_default_roles(self):
        """Initialize default roles in the RBAC system"""
        default_roles = [
            ("administrator", "Full system administration access"),
            ("moderator", "Content moderation and user management"),
            ("contributor", "Can create and edit content"),
            ("subscriber", "Basic read-only access")
        ]
        for role_name, description in default_roles:
            role = rbac_get_role_by_name(self.engine, role_name)
            if role is None:
                rbac_create_role(self.engine, role_name, description)
    
    def _get_user_id(self, username):
        """Get user ID from username"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if user:
                return user.id
        return None
    
    def _get_user_from_token(self):
        """Get username from stored token"""
        token = session.get(self._session_token_key)
        if not token:
            return None
        
        user_id = identitas_validate_token(self.engine, token)
        if not user_id:
            return None
        
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(id=user_id).first()
            if user:
                return user.username
        return None
    
    # -------------------------
    # User Management
    # -------------------------
    
    def create_user(self, username, password, role="subscriber", email=""):
        """
        Create a new user. Uses Identitas RBAC for role assignment.
        """
        token = identitas_register(self.engine, username, password, email)
        if token:
            # Use RBAC to assign role to user
            self._assign_role_to_user(username, role)
            return True, "User created"
        return False, "Username already taken or invalid password"
    
    def _assign_role_to_user(self, username, role_name):
        """Assign a role to a user using RBAC"""
        user_id = self._get_user_id(username)
        if not user_id:
            return False
        
        role = rbac_get_role_by_name(self.engine, role_name)
        if not role:
            # Create the role if it doesn't exist
            role = rbac_create_role(self.engine, role_name, f"Auto-created role: {role_name}")
        
        if role:
            return rbac_assign_role_to_user(self.engine, user_id, role.id)
        return False
    
    def _get_user_role(self, username):
        """Get user's primary role from RBAC"""
        user_id = self._get_user_id(username)
        if not user_id:
            return "subscriber"
        
        roles = rbac_get_user_roles(self.engine, user_id)
        if roles:
            # Return the first role (or highest priority one)
            return roles[0].name
        return "subscriber"
    
    def delete_user(self, username):
        """Delete user from Identitas database"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if user:
                db_session.delete(user)
                db_session.commit()
                return True, "User deleted"
        return False, "User not found"
    
    def change_password(self, username, new_password):
        """Change user password in Identitas database"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if not user:
                return False, "User not found"
            
            # Use Identitas password hashing
            from provider.api.auth import _hash_password
            hashed_pw, salt = _hash_password(new_password)
            user.password = hashed_pw
            user.salt = salt
            db_session.commit()
            return True, "Password changed"
    
    # -------------------------
    # Login / Logout
    # -------------------------
    
    def verify_login(self, username, password):
        """
        Verify login credentials. Returns True if valid, False otherwise.
        Note: This doesn't create a session - use login() for that.
        """
        token = identitas_login(self.engine, username, password)
        return token is not None
    
    def login(self, username):
        """
        Log in user by storing token in session.
        For backward compatibility, also store username in session.
        """
        # Get password from form (passed via session or re-authenticate)
        # For now, we store the username directly
        session[self._session_user_key] = username
        session.permanent = True
        
        # Also try to get/create a token if we have credentials
        # This is a workaround - in practice, login_action should pass the token
        if self._session_token_key not in session:
            # Try to generate a token by verifying with a stored credential
            # This is a limitation of the wrapper - full integration would need token passing
            pass
    
    def login_with_token(self, username, token):
        """Login with username and JWT token from Identitas"""
        # Validate token
        user_id = identitas_validate_token(self.engine, token)
        if not user_id:
            return False
        
        # Verify the token belongs to this user
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(id=user_id).first()
            if not user or user.username != username:
                return False
        
        session[self._session_user_key] = username
        session[self._session_token_key] = token
        session.permanent = True
        return True
    
    def logout(self):
        """Log out user by invalidating token and clearing session"""
        token = session.get(self._session_token_key)
        if token:
            identitas_logout(self.engine, token)
        
        session.pop(self._session_user_key, None)
        session.pop(self._session_token_key, None)
    
    def current_user(self):
        """Get the currently logged-in user from session"""
        # First check for direct username (backward compatibility)
        username = session.get(self._session_user_key)
        if username:
            return username
        
        # Otherwise try to get from token
        return self._get_user_from_token()
    
    # -------------------------
    # Role Management
    # -------------------------
    
    def get_user_role(self, username):
        """Get user's role"""
        return self._get_user_role(username)
    
    def update_user_role(self, username, role):
        """Update user's role using RBAC"""
        user_id = self._get_user_id(username)
        if not user_id:
            return False, "User not found"
        
        role_obj = rbac_get_role_by_name(self.engine, role)
        if not role_obj:
            # Create the role if it doesn't exist
            role_obj = rbac_create_role(self.engine, role, f"Auto-created role: {role}")
        
        if role_obj:
            # Remove all existing roles first (to ensure only one role at a time)
            existing_roles = rbac_get_user_roles(self.engine, user_id)
            for existing_role in existing_roles:
                rbac_remove_role_from_user(self.engine, user_id, existing_role.id)
            
            # Add the new role
            rbac_assign_role_to_user(self.engine, user_id, role_obj.id)
            return True, "Role updated"
        return False, "Failed to update role"
    
    def _set_user_role(self, username, role):
        """Set user's role (internal method)"""
        success, _ = self.update_user_role(username, role)
        return success
    
    def update_user_git_access(self, username, git_access):
        """Update user's git access (stored in role file)"""
        if git_access:
            # Give admin or elevated access
            current_role = self._get_user_role(username)
            if current_role != "administrator":
                self._set_user_role(username, "contributor")
        return True, "Git access updated"
    
    def has_git_access(self, username):
        """Check if user has git access"""
        role = self._get_user_role(username)
        if role == "administrator":
            return True
        return role in ("contributor", "moderator")
    
    def get_user(self, username):
        """Get full user object including email and role"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if not user:
                return None
            return {
                "username": user.username,
                "role": self._get_user_role(username),
                "email": user.email or "",
                "created_at": str(user.created_at) if hasattr(user, 'created_at') else ""
            }
    
    def update_email(self, username, email):
        """Update user's email address"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if not user:
                return False, "User not found"
            user.email = email
            db_session.commit()
            return True, "Email updated"
    
    def get_email(self, username):
        """Get user's email address"""
        with DBSession(self.engine) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if user:
                return user.email or ""
        return ""
    
    # -------------------------
    # Route Protection
    # -------------------------
    
    def require_login(self, f):
        """Decorator to require login for a route"""
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not self.current_user():
                return redirect(url_for("auth.login_page"))
            return f(*args, **kwargs)
        return wrapper
    
    def require_admin(self, f):
        """Decorator to require admin role for a route"""
        @wraps(f)
        def wrapper(*args, **kwargs):
            username = self.current_user()
            if not username:
                return redirect(url_for("auth.login_page"))
            if self.get_user_role(username) != "administrator":
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    
    def require_role(self, required_role):
        """Decorator to require a specific role for a route"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                user = session.get("user")
                if not user:
                    return redirect(url_for("auth.login_page"))
                user_role = self.get_user_role(user)
                role_hierarchy = {
                    "administrator": 5,
                    "moderator": 4,
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


# For backward compatibility - create default instance
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
auth = IdentitasAuthManager(BASE_PATH)