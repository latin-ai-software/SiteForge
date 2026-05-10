# lib/routes/admin/manage/notifications/index.py

import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from .....data.notification_manager import NotificationManager, NotificationType

admin_notifications_bp = Blueprint("admin_notifications", __name__, url_prefix="/admin/notifications")

# Auth-System initialisieren
BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))
auth = IdentitasAuthManager(BASE_PATH)
notification_manager = NotificationManager(BASE_PATH)

# LISTE: Alle Benachrichtigungen anzeigen
@admin_notifications_bp.route("/", methods=["GET"])
@auth.require_admin
def index():
    include_read = request.args.get('include_read', 'true').lower() == 'true'
    notifications = notification_manager.get_all_notifications(include_read=include_read)
    unread_count = notification_manager.get_unread_count()

    return render_template(
        "admin/notifications/index.html",
        notifications=notifications,
        unread_count=unread_count,
        include_read=include_read
    )

# POST: Neue Benachrichtigung erstellen
@admin_notifications_bp.route("/create", methods=["POST"])
@auth.require_admin
def create_notification():
    title = request.form.get("title", "").strip()
    message = request.form.get("message", "").strip()
    notification_type = request.form.get("type", "info")

    if not title or not message:
        flash("Titel und Nachricht sind erforderlich", "error")
        return redirect(url_for("admin_notifications.index"))

    try:
        notification_type_enum = NotificationType(notification_type)
    except ValueError:
        flash("Ungültiger Benachrichtigungstyp", "error")
        return redirect(url_for("admin_notifications.index"))

    success = notification_manager.create_notification(title, message, notification_type_enum)
    if success:
        flash("Benachrichtigung erfolgreich erstellt", "success")
    else:
        flash("Fehler beim Erstellen der Benachrichtigung", "error")

    return redirect(url_for("admin_notifications.index"))

# POST: Benachrichtigung als gelesen markieren
@admin_notifications_bp.route("/mark-read/<int:notification_id>", methods=["POST"])
@auth.require_admin
def mark_as_read(notification_id):
    success = notification_manager.mark_as_read(notification_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Benachrichtigung nicht gefunden"}), 404

# POST: Alle Benachrichtigungen als gelesen markieren
@admin_notifications_bp.route("/mark-all-read", methods=["POST"])
@auth.require_admin
def mark_all_as_read():
    success = notification_manager.mark_all_as_read()
    if success:
        flash("Alle Benachrichtigungen als gelesen markiert", "success")
    else:
        flash("Fehler beim Markieren der Benachrichtigungen", "error")

    return redirect(url_for("admin_notifications.index"))

# POST: Benachrichtigung löschen
@admin_notifications_bp.route("/delete/<int:notification_id>", methods=["POST"])
@auth.require_admin
def delete_notification(notification_id):
    success = notification_manager.delete_notification(notification_id)
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Benachrichtigung nicht gefunden"}), 404

# POST: Alle gelesenen Benachrichtigungen löschen
@admin_notifications_bp.route("/delete-read", methods=["POST"])
@auth.require_admin
def delete_read_notifications():
    success = notification_manager.delete_read_notifications()
    if success:
        flash("Alle gelesenen Benachrichtigungen wurden gelöscht", "success")
    else:
        flash("Fehler beim Löschen der Benachrichtigungen", "error")

    return redirect(url_for("admin_notifications.index"))

# API: Unread count für Badge
@admin_notifications_bp.route("/unread-count", methods=["GET"])
@auth.require_admin
def get_unread_count():
    count = notification_manager.get_unread_count()
    return jsonify({"count": count})