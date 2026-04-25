import os
import sys
import json
from flask import current_app
from ..netdefense.auth.identitas_auth import IdentitasAuthManager

# Add Identitas to path
IDENTITAS_PATH = os.path.join(os.path.dirname(__file__), "../../Identitas")
if IDENTITAS_PATH not in sys.path:
    sys.path.insert(0, IDENTITAS_PATH)

class UserManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.auth = IdentitasAuthManager(base_path)

    def get_all_users(self):
        """Get all users from Identitas database"""
        from sqlalchemy.orm import Session as DBSession
        from provider.models.user import User
        
        user_list = []
        with DBSession(self.auth.engine) as session:
            users = session.query(User).all()
            for user in users:
                user_list.append({
                    "username": user.username,
                    "role": self.auth._get_user_role(user.username),
                    "git_access": self.auth.has_git_access(user.username),
                    "created_at": str(user.created_at) if hasattr(user, 'created_at') else "Unknown"
                })
        return user_list

    def update_user_role(self, username, role):
        return self.auth.update_user_role(username, role)

    def update_user_git_access(self, username, git_access):
        return self.auth.update_user_git_access(username, git_access)

    def delete_user(self, username):
        return self.auth.delete_user(username)