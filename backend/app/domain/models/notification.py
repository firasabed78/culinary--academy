from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class NotificationType(str, enum.Enum):
    ENROLLMENT = "enrollment"
    PAYMENT = "payment"
    COURSE = "course"
    SYSTEM = "system"
    EMAIL = "email"
    SMS = "sms"

class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_type = Column(Enum(NotificationType), nullable=False)
    entity_id = Column(Integer, nullable=True)  # Related entity ID (enrollment, payment, etc.)
    entity_type = Column(String(50), nullable=True)  # Type of entity ("enrollment", "payment", etc.)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    class Config:
        orm_mode = True