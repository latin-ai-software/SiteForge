import os
import pickle

from flask.sessions import SessionInterface, SessionMixin


class RedisSessionInterface(SessionInterface):
    """Optional Redis-backed session store for multi-instance deployments."""

    def __init__(self, redis_client=None, prefix="session:", **kwargs):
        self.redis_client = redis_client
        self.prefix = prefix
        self.timeout = kwargs.get("timeout", 3600)

    def open_session(self, app, request):
        if self.redis_client is None:
            return None

        session_id = request.cookies.get(app.config.get("SESSION_COOKIE_NAME", "siteforge_session"))
        if not session_id:
            return app.session_interface.make_null_session(app)

        data = self.redis_client.get(f"{self.prefix}{session_id}")
        if not data:
            return app.session_interface.make_null_session(app)

        try:
            return pickle.loads(data)
        except Exception:
            return app.session_interface.make_null_session(app)

    def save_session(self, app, session, response):
        if self.redis_client is None:
            return

        if not session:
            return

        session_id = session.sid if hasattr(session, "sid") else None
        if not session_id:
            return

        data = pickle.dumps(dict(session))
        self.redis_client.setex(f"{self.prefix}{session_id}", self.timeout, data)
