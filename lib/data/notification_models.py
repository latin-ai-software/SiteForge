# lib/data/notification_models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from Identitas.provider.backend.db_operations import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum
from datetime import datetime
import enum

class NotificationType(enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    ALERT = "alert"

class Notification(Base):
    """Admin notification system"""
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.INFO)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type={self.type}, read={self.is_read})>"