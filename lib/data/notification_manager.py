# lib/data/notification_manager.py

import os
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from .notification_models import Notification, NotificationType

class NotificationManager:
    """Manager for admin notifications"""

    def __init__(self, base_path):
        self.base_path = base_path
        self.auth = IdentitasAuthManager(base_path)

    def create_notification(self, title: str, message: str, notification_type: NotificationType = NotificationType.INFO) -> bool:
        """Create a new notification"""
        try:
            with DBSession(self.auth.engine) as session:
                notification = Notification(
                    title=title,
                    message=message,
                    type=notification_type
                )
                session.add(notification)
                session.commit()
                return True
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False

    def get_all_notifications(self, include_read: bool = True):
        """Get all notifications, optionally filtering by read status"""
        try:
            with DBSession(self.auth.engine) as session:
                query = session.query(Notification).order_by(Notification.created_at.desc())
                if not include_read:
                    query = query.filter_by(is_read=False)
                return query.all()
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        try:
            with DBSession(self.auth.engine) as session:
                return session.query(Notification).filter_by(is_read=False).count()
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0

    def mark_as_read(self, notification_id: int) -> bool:
        """Mark a notification as read"""
        try:
            with DBSession(self.auth.engine) as session:
                notification = session.query(Notification).filter_by(id=notification_id).first()
                if notification:
                    notification.is_read = True
                    notification.read_at = datetime.utcnow()
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False

    def mark_all_as_read(self) -> bool:
        """Mark all notifications as read"""
        try:
            with DBSession(self.auth.engine) as session:
                session.query(Notification).filter_by(is_read=False).update({
                    'is_read': True,
                    'read_at': datetime.utcnow()
                })
                session.commit()
                return True
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return False

    def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        try:
            with DBSession(self.auth.engine) as session:
                notification = session.query(Notification).filter_by(id=notification_id).first()
                if notification:
                    session.delete(notification)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Error deleting notification: {e}")
            return False

    def delete_read_notifications(self) -> bool:
        """Delete all read notifications"""
        try:
            with DBSession(self.auth.engine) as session:
                session.query(Notification).filter_by(is_read=True).delete()
                session.commit()
                return True
        except Exception as e:
            print(f"Error deleting read notifications: {e}")
            return False