# lib/notification_utils.py

"""
Utility functions for creating admin notifications
"""

from lib.data.notification_manager import NotificationManager, NotificationType

def create_admin_notification(base_path: str, title: str, message: str, notification_type: NotificationType = NotificationType.INFO):
    """
    Create an admin notification

    Args:
        base_path: Base path of the application
        title: Notification title
        message: Notification message
        notification_type: Type of notification (INFO, WARNING, ERROR, SUCCESS, ALERT)
    """
    try:
        manager = NotificationManager(base_path)
        return manager.create_notification(title, message, notification_type)
    except Exception as e:
        print(f"Failed to create notification: {e}")
        return False

def notify_system_alert(base_path: str, message: str):
    """Create an alert notification for system issues"""
    return create_admin_notification(
        base_path,
        "System Alert",
        message,
        NotificationType.ALERT
    )

def notify_security_issue(base_path: str, message: str):
    """Create a security warning notification"""
    return create_admin_notification(
        base_path,
        "Security Warning",
        message,
        NotificationType.WARNING
    )

def notify_error(base_path: str, message: str):
    """Create an error notification"""
    return create_admin_notification(
        base_path,
        "System Error",
        message,
        NotificationType.ERROR
    )

def notify_success(base_path: str, message: str):
    """Create a success notification"""
    return create_admin_notification(
        base_path,
        "Success",
        message,
        NotificationType.SUCCESS
    )

def notify_info(base_path: str, message: str):
    """Create an info notification"""
    return create_admin_notification(
        base_path,
        "Information",
        message,
        NotificationType.INFO
    )