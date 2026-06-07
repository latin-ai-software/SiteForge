import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import lib.routes.root.auth as auth_module


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "testsecret"
    app.config["TESTING"] = True
    return app


def test_login_action_missing_fields(app):
    with app.test_request_context("/login", method="POST", data={}):
        with patch.object(auth_module, "render_template", return_value="rendered") as mock_render:
            response, status = auth_module.login_action()

            assert status == 400
            mock_render.assert_called_once_with("auth/login.html", error="Username and password required")


def test_login_action_invalid_username(app):
    with app.test_request_context("/login", method="POST", data={"username": "bad user", "password": "pass"}):
        with patch.object(auth_module, "InputValidator") as mock_validator, patch.object(auth_module, "render_template", return_value="rendered") as mock_render:
            mock_validator.validate_username.return_value = False

            response, status = auth_module.login_action()

            assert status == 400
            mock_render.assert_called_once_with("auth/login.html", error="Invalid username format")


def test_login_action_rate_limited_ip(app):
    with app.test_request_context("/login", method="POST", data={"username": "testuser", "password": "secret"}, environ_overrides={"REMOTE_ADDR": "127.0.0.1"}):
        with patch.object(auth_module, "InputValidator") as mock_validator, patch.object(auth_module, "rate_limiter") as mock_rate_limiter, patch.object(auth_module, "render_template", return_value="rendered") as mock_render:
            mock_validator.validate_username.return_value = True
            mock_rate_limiter.check_login_attempt.return_value = (True, "Locked out")
            mock_rate_limiter.is_rate_limited.return_value = False

            response, status = auth_module.login_action()

            assert status == 429
            mock_render.assert_called_once_with("auth/login.html", error="Locked out")


def test_login_action_success(app):
    with app.test_request_context("/login", method="POST", data={"username": "testuser", "password": "secret"}, environ_overrides={"REMOTE_ADDR": "127.0.0.1"}):
        with patch.object(auth_module, "InputValidator") as mock_validator, patch.object(auth_module, "rate_limiter") as mock_rate_limiter, patch("Identitas.provider.api.auth.login", return_value="token") as mock_login, patch.object(auth_module, "auth") as mock_auth, patch.object(auth_module, "redirect", return_value="redirected") as mock_redirect, patch.object(auth_module, "url_for", return_value="/") as mock_url_for:
            mock_validator.validate_username.return_value = True
            mock_rate_limiter.check_login_attempt.return_value = (False, None)
            mock_rate_limiter.is_rate_limited.return_value = False
            mock_auth.login_with_token.return_value = True

            result = auth_module.login_action()

            assert result == "redirected"
            mock_auth.login_with_token.assert_called_once_with("testuser", "token")
            mock_url_for.assert_called_once_with("root.index")


def test_register_action_missing_fields(app):
    with app.test_request_context("/register", method="POST", data={"username": "", "password": "", "email": ""}):
        with patch.object(auth_module, "render_template", return_value="rendered") as mock_render:
            response, status = auth_module.register_action()

            assert status == 400
            mock_render.assert_called_once_with("auth/register.html", error="Username, email and password required")


def test_register_action_success(app):
    with app.test_request_context("/register", method="POST", data={"username": "testuser", "password": "Secret123!", "email": "test@example.com"}, environ_overrides={"REMOTE_ADDR": "127.0.0.1"}):
        with patch.object(auth_module, "InputValidator") as mock_validator, patch.object(auth_module, "rate_limiter") as mock_rate_limiter, patch("Identitas.provider.api.auth.register", return_value="token") as mock_register, patch.object(auth_module, "auth") as mock_auth, patch.object(auth_module, "redirect", return_value="redirected") as mock_redirect, patch.object(auth_module, "url_for", return_value="/"):
            mock_validator.validate_username.return_value = True
            mock_validator.validate_email.return_value = True
            mock_validator.validate_password.return_value = (True, "Strong password")
            mock_rate_limiter.is_rate_limited.return_value = False

            result = auth_module.register_action()

            assert result == "redirected"
            mock_auth._assign_role_to_user.assert_called_once_with("testuser", "subscriber")
            mock_auth.login_with_token.assert_called_once_with("testuser", "token")


def test_logout_redirects(app):
    with app.test_request_context("/logout"):
        with patch.object(auth_module, "auth") as mock_auth, patch.object(auth_module, "redirect", return_value="redirected") as mock_redirect, patch.object(auth_module, "url_for", return_value="/"):
            result = auth_module.logout()

            assert result == "redirected"
            mock_auth.logout.assert_called_once()


def test_change_password_redirects_to_login_when_not_logged_in(app):
    with app.test_request_context("/change-password"):
        with patch.object(auth_module, "redirect", return_value="redirected") as mock_redirect, patch.object(auth_module, "url_for", return_value="/login"):
            result = auth_module.change_password()

            assert result == "redirected"
