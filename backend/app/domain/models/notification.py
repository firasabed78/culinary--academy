"""
notification.py - Notification model definition
This file defines the SQLAlchemy ORM model for user notifications in the system.
It includes a type enum for categorizing notifications, tracks notification
metadata such as read status and creation time, and establishes relationships
with users. The notification system enables communication with users about
important events like enrollment changes, payments, and system announcements.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Boolean, Enum  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
from sqlalchemy.sql import func  # Import SQL functions for default timestamps
import enum  # Import Python's enum module for type definitions
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class NotificationType(str, enum.Enum):
    """
    Enumeration of notification types in the system.
    Categorizes notifications based on their source and purpose.
    """
    ENROLLMENT = "enrollment"  # Notifications related to course enrollments (approval, rejection, etc.)
    PAYMENT = "payment"        # Notifications about payment status (successful, failed, refunded)
    COURSE = "course"          # Notifications about course updates (schedule changes, new materials)
    SYSTEM = "system"          # System-level notifications (maintenance, policy updates)
    EMAIL = "email"            # Email notifications (sent via email in addition to in-app)
    SMS = "sms"                # SMS notifications (sent via text message in addition to in-app)

class Notification(Base):
    """User notifications."""
    __tablename__ = "notifications"  # Database table name for notifications
    
    # Primary key and basic notification information
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Foreign key to the notification recipient
    
    # Notification content
    title = Column(String(255), nullable=False)  # Short notification title/subject
    message = Column(Text, nullable=False)       # Detailed notification message content
    
    # Notification status and metadata
    is_read = Column(Boolean, default=False)  # Flag indicating if user has read the notification
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Automatic timestamp when notification is created
    notification_type = Column(Enum(NotificationType), nullable=False)  # Category of notification from predefined types
    
    # Related entity references (polymorphic relationship)
    entity_id = Column(Integer, nullable=True)    # ID of the related entity (enrollment, payment, etc.)
    entity_type = Column(String(50), nullable=True)  # Type of the related entity for polymorphic lookup
    
    # Relationships
    user = relationship("User", back_populates="notifications")  # Bi-directional relationship with User model
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration