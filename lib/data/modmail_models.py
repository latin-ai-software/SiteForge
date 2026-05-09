# lib/data/modmail_models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from Identitas.provider.backend.db_operations import Base

class ModmailSubject(Base):
    """Available subjects for modmail conversations"""
    __tablename__ = "modmail_subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModmailConversation(Base):
    """Modmail conversation thread"""
    __tablename__ = "modmail_conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject_id = Column(Integer, ForeignKey('modmail_subjects.id'), nullable=False)
    title = Column(String, nullable=False)
    is_open = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="modmail_conversations")
    subject = relationship("ModmailSubject", backref="conversations")
    messages = relationship("ModmailMessage", back_populates="conversation", cascade="all, delete-orphan")

class ModmailMessage(Base):
    """Individual messages in a modmail conversation"""
    __tablename__ = "modmail_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('modmail_conversations.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)  # Encrypted content
    iv = Column(String, nullable=False)  # Initialization vector for encryption
    salt = Column(String, nullable=False)  # Salt used for key derivation
    is_from_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("ModmailConversation", back_populates="messages")
    sender = relationship("User", backref="modmail_messages")