#!/usr/bin/env python3
"""
Test script for the admin notification system
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

def test_notifications():
    """Test the notification system"""
    from lib.data.notification_manager import NotificationManager, NotificationType
    from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

    base_path = os.path.abspath('.')
    auth = IdentitasAuthManager(base_path)
    manager = NotificationManager(base_path)

    print("Testing notification system...")

    # Test creating a notification
    print("Creating test notification...")
    success = manager.create_notification(
        "Test Notification",
        "This is a test notification to verify the system works.",
        NotificationType.INFO
    )

    if success:
        print("✓ Notification created successfully")
    else:
        print("✗ Failed to create notification")
        return False

    # Test getting notifications
    print("Getting notifications...")
    notifications = manager.get_all_notifications()
    print(f"Found {len(notifications)} notifications")

    if len(notifications) > 0:
        print("✓ Notifications retrieved successfully")
        print(f"Latest notification: {notifications[0].title}")
    else:
        print("✗ No notifications found")
        return False

    # Test unread count
    print("Checking unread count...")
    unread_count = manager.get_unread_count()
    print(f"Unread notifications: {unread_count}")

    # Test marking as read
    if len(notifications) > 0 and not notifications[0].is_read:
        print("Marking notification as read...")
        success = manager.mark_as_read(notifications[0].id)
        if success:
            print("✓ Notification marked as read")
            new_unread_count = manager.get_unread_count()
            print(f"New unread count: {new_unread_count}")
        else:
            print("✗ Failed to mark notification as read")

    print("Notification system test completed!")
    return True

if __name__ == "__main__":
    test_notifications()