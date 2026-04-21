import os
import json
from flask import current_app
from ..netdefense.auth.provider import AuthManager

class UserManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.auth = AuthManager(base_path)

    def get_all_users(self):
        users = self.auth._load()
        user_list = []
        for username, data in users.items():
            user_list.append({
                "username": username,
                "role": data.get("role", "subscriber"),
                "git_access": data.get("git_access", False),
                "created_at": data.get("created_at", "Unknown")
            })
        return user_list

    def update_user_role(self, username, role):
        return self.auth.update_user_role(username, role)

    def update_user_git_access(self, username, git_access):
        return self.auth.update_user_git_access(username, git_access)

    def delete_user(self, username):
        return self.auth.delete_user(username)