#!/usr/bin/env python3
"""
Admin Rescue Script

This script allows you to regain admin access if you accidentally lock yourself out
by resetting the admin role for a specified user.

Usage:
    python admin_rescue.py <username>

Requirements:
    - Run this script from the project root directory
    - The user must exist in the system
    - You'll need to provide the admin password to confirm

Security Note:
    This script should only be used in emergency situations when admin access is lost.
    After using this script, change your password immediately.
"""

import sys
import os
import getpass

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    if len(sys.argv) != 2:
        print("Usage: python admin_rescue.py <username>")
        print("Example: python admin_rescue.py admin")
        sys.exit(1)

    username = sys.argv[1]

    try:
        from lib.netdefense.auth.identitas_auth import IdentitasAuthManager

        # Initialize auth manager
        base_path = os.path.dirname(os.path.abspath(__file__))
        auth = IdentitasAuthManager(base_path)

        # Check if user exists
        user_info = auth.get_user(username)
        if not user_info:
            print(f"❌ User '{username}' does not exist")
            sys.exit(1)

        print(f"Found user: {username}")
        print(f"Current role: {user_info['role']}")

        # Verify the user knows the password (security check)
        password = getpass.getpass("Enter the user's password to confirm: ")
        if not auth.verify_login(username, password):
            print("❌ Incorrect password")
            sys.exit(1)

        # Reset to administrator role
        success, message = auth.update_user_role(username, 'administrator')
        if success:
            print("✅ Successfully restored administrator access!")
            print(f"User '{username}' now has administrator role")
        else:
            print(f"❌ Failed to restore admin access: {message}")
            sys.exit(1)

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()