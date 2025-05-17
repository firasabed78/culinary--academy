"""
notification_service.py - Service layer for notification management
This file handles business logic related to user notifications, including
sending, updating, filtering, and email dispatch features. It provides 
an abstraction over the notification repository and integrates with 
the email service.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.domain.models.notification import Notification, NotificationType  # Import notification models
from app.domain.schemas.notification import NotificationCreate, NotificationUpdate  # Import notification schemas
from app.repositories.notification_repository import NotificationRepository  # Import repository for database operations
from app.services.base import BaseService  # Import base service for common functionality
from app.core.exceptions import NotFoundError  # Import custom exception for not found errors
from app.services.email_service import EmailService  # Import email service for notification emails

class NotificationService(BaseService[Notification, NotificationCreate, NotificationUpdate, NotificationRepository]):
    """Service for notification operations."""
    
    def __init__(self):
        # Initialize with notification repository
        super().__init__(NotificationRepository)
        # Create an instance of email service for sending notification emails
        self.email_service = EmailService()
    
    def get_with_user(self, db: Session, id: int) -> Optional[Notification]:
        """Get a notification with user data."""
        # Retrieve notification with associated user data
        notification = self.repository.get_with_user(db, id)
        # Raise an exception if notification not found
        if not notification:
            raise NotFoundError(detail="Notification not found")
        # Return found notification with user data
        return notification
    
    def create_notification(
        self, db: Session, *, obj_in: NotificationCreate, send_email: bool = False
    ) -> Notification:
        """Create a new notification with optional email."""
        # Create notification in database using repository
        notification = self.repository.create(db, obj_in=obj_in)
        
        # Send email if requested and user has email
        if send_email and notification.user.email:
            self.email_service.send_notification_email(
                email_to=notification.user.email,
                subject=notification.title,
                body=notification.message
            )
        # Return the created notification
        return notification
    
    def mark_as_read(self, db: Session, *, id: int) -> Notification:
        """Mark a notification as read."""
        # Find notification by ID
        notification = self.repository.get(db, id)
        # Raise exception if notification not found
        if not notification:
            raise NotFoundError(detail="Notification not found")
        # Update notification as read and return updated object
        return self.repository.mark_as_read(db, db_obj=notification)
    
    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        """Mark all notifications for a user as read."""
        # Mark all user's notifications as read and return count of updated records
        return self.repository.mark_all_as_read(db, user_id=user_id)
    
    def get_user_notifications(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100, unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        # If unread_only flag is set, get only unread notifications
        if unread_only:
            return self.repository.get_unread_by_user(db, user_id=user_id, skip=skip, limit=limit)
        # Otherwise get all notifications for the user with pagination
        return self.repository.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def count_unread(self, db: Session, *, user_id: int) -> int:
        """Count unread notifications for a user."""
        # Get count of unread notifications for a specific user
        return self.repository.count_unread_by_user(db, user_id=user_id)
    
    def get_filtered_notifications(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Notification]:
        """Get notifications with filtering."""
        # Get notifications with applied filters and pagination
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)
    
    def create_system_notification(
        self, db: Session, *, user_id: int, title: str, message: str,
        send_email: bool = False, entity_id: Optional[int] = None,
        entity_type: Optional[str] = None
    ) -> Notification:
        """Create a system notification."""
        # Create notification data object with system type
        notification_data = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.SYSTEM,  # Set notification type as SYSTEM
            entity_id=entity_id,  # Optional related entity ID
            entity_type=entity_type,  # Optional related entity type
            is_read=False  # Set as unread by default
        )
        # Use create_notification method to create and optionally send email
        return self.create_notification(db, obj_in=notification_data, send_email=send_email)