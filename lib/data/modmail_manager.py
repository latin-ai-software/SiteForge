# lib/data/modmail_manager.py

import os
import json
from datetime import datetime
from sqlalchemy.orm import Session as DBSession
from lib.netdefense.auth.identitas_auth import IdentitasAuthManager
from lib.modmail_crypto import ModmailCrypto

# Import models to ensure they're registered with SQLAlchemy
from Identitas.provider.models.user import User
from Identitas.provider.models.role import Role
from lib.data.modmail_models import ModmailSubject, ModmailConversation, ModmailMessage

class ModmailManager:
    """Manager for modmail functionality with end-to-end encryption"""

    def __init__(self, base_path):
        self.base_path = base_path
        self.auth = IdentitasAuthManager(base_path)
        self.crypto = ModmailCrypto()

    def is_modmail_enabled(self) -> bool:
        """Check if modmail is enabled in settings"""
        settings_file = os.path.join(self.base_path, "data", "settings.json")
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    return settings.get("modmail_enabled", False)
            except:
                pass
        return False

    def set_modmail_enabled(self, enabled: bool) -> bool:
        """Enable or disable modmail"""
        settings_file = os.path.join(self.base_path, "data", "settings.json")
        os.makedirs(os.path.dirname(settings_file), exist_ok=True)

        # Load existing settings
        settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            except:
                settings = {}

        # Update modmail setting
        settings["modmail_enabled"] = enabled

        # Save settings
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False

    def get_subjects(self) -> list:
        """Get all active modmail subjects"""
        from lib.data.modmail_models import ModmailSubject

        with DBSession(self.auth.engine) as session:
            subjects = session.query(ModmailSubject).filter_by(is_active=True).all()
            return [{
                'id': s.id,
                'name': s.name,
                'description': s.description
            } for s in subjects]

    def create_subject(self, name: str, description: str = "") -> tuple[bool, str]:
        """Create a new modmail subject"""
        from lib.data.modmail_models import ModmailSubject

        with DBSession(self.auth.engine) as session:
            # Check if subject already exists
            existing = session.query(ModmailSubject).filter_by(name=name).first()
            if existing:
                return False, "Subject already exists"

            subject = ModmailSubject(name=name, description=description)
            session.add(subject)
            session.commit()
            return True, "Subject created"

    def update_subject(self, subject_id: int, name: str = None, description: str = None, is_active: bool = None) -> tuple[bool, str]:
        """Update a modmail subject"""
        from lib.data.modmail_models import ModmailSubject

        with DBSession(self.auth.engine) as session:
            subject = session.query(ModmailSubject).filter_by(id=subject_id).first()
            if not subject:
                return False, "Subject not found"

            if name is not None:
                subject.name = name
            if description is not None:
                subject.description = description
            if is_active is not None:
                subject.is_active = is_active

            session.commit()
            return True, "Subject updated"

    def delete_subject(self, subject_id: int) -> tuple[bool, str]:
        """Delete a modmail subject"""
        from lib.data.modmail_models import ModmailSubject

        with DBSession(self.auth.engine) as session:
            subject = session.query(ModmailSubject).filter_by(id=subject_id).first()
            if not subject:
                return False, "Subject not found"

            session.delete(subject)
            session.commit()
            return True, "Subject deleted"

    def create_conversation(self, user_id: int, subject_id: int, title: str, initial_message: str, user_password: str) -> tuple[bool, str]:
        """Create a new modmail conversation"""
        from lib.data.modmail_models import ModmailConversation, ModmailMessage

        with DBSession(self.auth.engine) as session:
            # Verify subject exists
            from lib.data.modmail_models import ModmailSubject
            subject = session.query(ModmailSubject).filter_by(id=subject_id, is_active=True).first()
            if not subject:
                return False, "Invalid subject"

            # Create conversation
            conversation = ModmailConversation(
                user_id=user_id,
                subject_id=subject_id,
                title=title
            )
            session.add(conversation)
            session.flush()  # Get conversation ID

            # Encrypt and add initial message
            encrypted_data = self.crypto.encrypt_message(initial_message, user_password)

            message = ModmailMessage(
                conversation_id=conversation.id,
                sender_id=user_id,
                content=encrypted_data['ciphertext'],
                iv=encrypted_data['iv'],
                salt=encrypted_data['salt'],
                is_from_admin=False
            )
            session.add(message)
            session.commit()

            return True, f"Conversation created with ID {conversation.id}"

    def add_message(self, conversation_id: int, sender_id: int, content: str, password: str, is_from_admin: bool = False) -> tuple[bool, str]:
        """Add a message to a conversation"""
        from lib.data.modmail_models import ModmailConversation, ModmailMessage

        with DBSession(self.auth.engine) as session:
            # Verify conversation exists and is open
            conversation = session.query(ModmailConversation).filter_by(id=conversation_id, is_open=True).first()
            if not conversation:
                return False, "Conversation not found or closed"

            # Encrypt message
            encrypted_data = self.crypto.encrypt_message(content, password)

            message = ModmailMessage(
                conversation_id=conversation_id,
                sender_id=sender_id,
                content=encrypted_data['ciphertext'],
                iv=encrypted_data['iv'],
                salt=encrypted_data['salt'],
                is_from_admin=is_from_admin
            )
            session.add(message)
            session.commit()

            return True, "Message added"

    def get_conversations_for_user(self, user_id: int) -> list:
        """Get all conversations for a user"""
        from lib.data.modmail_models import ModmailConversation

        with DBSession(self.auth.engine) as session:
            conversations = session.query(ModmailConversation).filter_by(user_id=user_id).all()
            return [{
                'id': c.id,
                'subject': c.subject.name,
                'title': c.title,
                'is_open': c.is_open,
                'created_at': str(c.created_at),
                'message_count': len(c.messages)
            } for c in conversations]

    def get_conversations_for_admin(self) -> list:
        """Get all conversations for admin view"""
        from lib.data.modmail_models import ModmailConversation

        with DBSession(self.auth.engine) as session:
            conversations = session.query(ModmailConversation).all()
            return [{
                'id': c.id,
                'user': c.user.username,
                'subject': c.subject.name,
                'title': c.title,
                'is_open': c.is_open,
                'created_at': str(c.created_at),
                'message_count': len(c.messages)
            } for c in conversations]

    def get_conversation_messages(self, conversation_id: int, password: str) -> list:
        """Get decrypted messages for a conversation"""
        from lib.data.modmail_models import ModmailMessage

        with DBSession(self.auth.engine) as session:
            messages = session.query(ModmailMessage).filter_by(conversation_id=conversation_id).order_by(ModmailMessage.created_at).all()

            decrypted_messages = []
            for msg in messages:
                try:
                    encrypted_data = {
                        'ciphertext': msg.content,
                        'iv': msg.iv,
                        'salt': msg.salt
                    }
                    content = self.crypto.decrypt_message(encrypted_data, password)

                    decrypted_messages.append({
                        'id': msg.id,
                        'sender': msg.sender.username,
                        'content': content,
                        'is_from_admin': msg.is_from_admin,
                        'created_at': str(msg.created_at)
                    })
                except:
                    # If decryption fails, show placeholder
                    decrypted_messages.append({
                        'id': msg.id,
                        'sender': msg.sender.username,
                        'content': '[Encrypted message - unable to decrypt]',
                        'is_from_admin': msg.is_from_admin,
                        'created_at': str(msg.created_at)
                    })

            return decrypted_messages

    def close_conversation(self, conversation_id: int) -> tuple[bool, str]:
        """Close a modmail conversation"""
        from lib.data.modmail_models import ModmailConversation

        with DBSession(self.auth.engine) as session:
            conversation = session.query(ModmailConversation).filter_by(id=conversation_id).first()
            if not conversation:
                return False, "Conversation not found"

            conversation.is_open = False
            session.commit()
            return True, "Conversation closed"