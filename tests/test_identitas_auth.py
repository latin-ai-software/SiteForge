import pytest
from unittest.mock import patch, MagicMock
from werkzeug.exceptions import HTTPException
from flask import Flask, session
from sqlalchemy import create_engine, inspect, text

from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from Identitas.provider.backend.db_operations import create_sqlite_database


@pytest.fixture
def auth_manager(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    monkeypatch.setattr('lib.netdefense.auth.identitas_auth.create_sqlite_database', lambda path: engine)
    monkeypatch.setattr('lib.netdefense.auth.identitas_auth.rbac_get_role_by_name', lambda engine, role: None)
    monkeypatch.setattr('lib.netdefense.auth.identitas_auth.rbac_create_role', lambda engine, role, desc: MagicMock(id=1))
    return IdentitasAuthManager(str(tmp_path))


def test_require_login_redirects_when_not_authenticated(auth_manager):
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'

    @app.route('/login', endpoint='auth.login_page')
    def login_page():
        return 'login'

    @app.route('/protected')
    @auth_manager.require_login
    def protected():
        return 'ok'

    client = app.test_client()
    response = client.get('/protected')

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')


def test_require_admin_aborts_for_non_admin(auth_manager):
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'

    @app.route('/login', endpoint='auth.login_page')
    def login_page():
        return 'login'

    @app.route('/admin-only')
    @auth_manager.require_admin
    def admin_only():
        return 'admin'

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = 'user'

    with patch.object(auth_manager, 'get_user_role', return_value='subscriber'):
        response = client.get('/admin-only')

    assert response.status_code == 403


def test_require_role_blocks_insufficient_role_and_allows_higher(auth_manager):
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'

    @app.route('/login', endpoint='auth.login_page')
    def login_page():
        return 'login'

    @app.route('/protected-role')
    @auth_manager.require_role('contributor')
    def protected_role():
        return 'ok'

    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user'] = 'user'

    with patch.object(auth_manager, 'get_user_role', return_value='subscriber'):
        response = client.get('/protected-role')
        assert response.status_code == 403

    with patch.object(auth_manager, 'get_user_role', return_value='administrator'):
        response = client.get('/protected-role')
        assert response.status_code == 200
        assert response.data == b'ok'


def test_logout_clears_session_and_invalidates_token(auth_manager):
    app = Flask(__name__)
    app.secret_key = 'test-secret-key'

    with app.test_request_context('/logout'):
        session['user'] = 'user'
        session['identitas_token'] = 'token'
        assert session.get(auth_manager._session_token_key) == 'token'

        with patch('lib.netdefense.auth.identitas_auth.identitas_logout') as mock_logout:
            auth_manager.logout()

        assert 'user' not in session
        assert 'identitas_token' not in session
        assert mock_logout.call_count in (0, 1)


def test_create_sqlite_database_migrates_legacy_users_table(tmp_path):
    db_path = tmp_path / 'legacy_identitas.db'
    with create_engine(f'sqlite:///{db_path}').begin() as conn:
        conn.execute(text('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                email TEXT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                salt TEXT NOT NULL
            )
        '''))

    engine = create_sqlite_database(str(db_path))
    with engine.begin() as conn:
        columns = {row['name'] for row in inspect(conn).get_columns('users')}

    assert {'public_key', 'public_key_fingerprint', 'key_auth_enabled'}.issubset(columns)
