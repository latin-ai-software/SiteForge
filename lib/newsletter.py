import os
import json
import re
import smtplib
from email.message import EmailMessage
from flask import current_app, request


def load_settings():
    settings_file = os.path.join(current_app.root_path, "data", "settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            current_app.logger.exception("Failed to load settings for newsletter")
    return {}


def get_newsletter_subscribers_path():
    return os.path.join(current_app.root_path, "data", "newsletter_subscribers.json")


def load_newsletter_subscribers():
    path = get_newsletter_subscribers_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            current_app.logger.exception("Failed to load newsletter subscribers")
    return []


def save_newsletter_subscribers(subscribers):
    path = get_newsletter_subscribers_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sorted(set(subscribers)), f, indent=2)
        return True
    except Exception:
        current_app.logger.exception("Failed to save newsletter subscribers")
        return False


def normalize_email(email):
    return email.strip().lower()


def is_valid_email(email):
    return bool(re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def subscribe_email(email):
    email = normalize_email(email)
    if not email or not is_valid_email(email):
        return False, "Bitte geben Sie eine gültige E-Mail-Adresse ein."

    subscribers = load_newsletter_subscribers()
    if email in subscribers:
        return False, "Diese E-Mail-Adresse ist bereits angemeldet."

    subscribers.append(email)
    if save_newsletter_subscribers(subscribers):
        return True, "Danke! Du wurdest zum Newsletter hinzugefügt."
    return False, "Fehler beim Speichern der Anmeldung. Bitte versuche es später erneut."


def get_base_url():
    settings = load_settings()
    domain = settings.get("domain", "") or ""
    if domain:
        domain = domain.strip()
        if domain.startswith("http://") or domain.startswith("https://"):
            return domain.rstrip("/")
        return f"https://{domain.rstrip('/') if domain else ''}"

    try:
        return request.host_url.rstrip("/")
    except RuntimeError:
        return "http://localhost:5000"


def send_newsletter(subject, html_body, text_body=None, recipients=None):
    settings = load_settings()
    if not settings.get("newsletter_enabled"):
        current_app.logger.info("Newsletter sending disabled in settings")
        return False

    if recipients is None:
        recipients = load_newsletter_subscribers()

    if not recipients:
        current_app.logger.info("Newsletter send skipped because no subscribers")
        return False

    sender = settings.get("newsletter_sender_email", "")
    host = settings.get("ses_smtp_host", "")
    port = int(settings.get("ses_smtp_port", 587) or 587)
    username = settings.get("ses_smtp_username", "")
    password = settings.get("ses_smtp_password", "")

    if not sender or not host or not username or not password:
        current_app.logger.warning("Newsletter not sent: SES settings incomplete")
        return False

    for recipient in recipients:
        try:
            message = EmailMessage()
            message["From"] = sender
            message["To"] = recipient
            message["Subject"] = subject
            message.set_content(text_body or html_body)
            message.add_alternative(html_body, subtype="html")

            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=20)
            else:
                server = smtplib.SMTP(host, port, timeout=20)
                server.starttls()

            server.login(username, password)
            server.send_message(message)
            server.quit()
        except Exception:
            current_app.logger.exception(f"Failed to send newsletter to {recipient}")
            continue

    return True


def get_newsletter_subscriber_count():
    return len(load_newsletter_subscribers())
