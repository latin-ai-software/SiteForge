import os
import sys
import json
from flask import current_app
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

# Add Intermediarium cache
try:
    from Intermediarium import Cache
    _cache_available = True
except ImportError:
    _cache_available = False

# Add Identitas project root to path so Identitas can be imported consistently
IDENTITAS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Identitas"))
IDENTITAS_ROOT = os.path.abspath(os.path.dirname(IDENTITAS_PATH))
for path_entry in (IDENTITAS_ROOT, IDENTITAS_PATH):
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

class UserManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.auth = IdentitasAuthManager(base_path)
        # Initialize cache for user data (1 hour TTL)
        if _cache_available:
            self._user_cache = Cache(maxsize=500, policy='lru', ttl=3600)
        else:
            self._user_cache = None

    def get_all_users(self):
        """Get all users from Identitas database (cached)"""
        # Check cache first
        if self._user_cache is not None:
            cached_users = self._user_cache.get('all_users')
            if cached_users is not None:
                return cached_users
        
        from sqlalchemy.orm import Session as DBSession
        from Identitas.provider.models.user import User
        
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
        
        # Cache the result
        if self._user_cache is not None:
            self._user_cache.set('all_users', user_list)
        
        return user_list

    def update_user_role(self, username, role):
        success, message = self.auth.update_user_role(username, role)
        # Invalidate cache on update
        if self._user_cache is not None:
            self._user_cache.delete('all_users')
        # Also clear global caches
        try:
            from lib.cache_utils import clear_all_caches
            clear_all_caches()
        except Exception:
            pass
        return success, message

    def update_user_git_access(self, username, git_access):
        success, message = self.auth.update_user_git_access(username, git_access)
        # Invalidate cache on update
        if self._user_cache is not None:
            self._user_cache.delete('all_users')
        # Also clear global caches
        try:
            from lib.cache_utils import clear_all_caches
            clear_all_caches()
        except Exception:
            pass
        return success, message

    def delete_user(self, username):
        result = self.auth.delete_user(username)
        # Invalidate cache on delete
        if self._user_cache is not None:
            self._user_cache.delete('all_users')
        # Also clear global caches
        try:
            from lib.cache_utils import clear_all_caches
            clear_all_caches()
        except Exception:
            pass
        return result
    
    def clear_cache(self):
        """Clear user cache manually"""
        if self._user_cache is not None:
            self._user_cache.clear()