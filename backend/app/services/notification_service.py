from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.models.notification import Notification, NotificationType
from app.domain.schemas.notification import NotificationCreate, NotificationUpdate
from app.repositories.notification_repository import NotificationRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError
from app.services.email_service import EmailService


class NotificationService(BaseService[Notification, NotificationCreate, NotificationUpdate, NotificationRepository]):
    """Service for notification operations."""
    
    def __init__(self):
        super().__init__(NotificationRepository)
        self.email_service = EmailService()
    
    def get_with_user(self, db: Session, id: int) -> Optional[Notification]:
        """Get a notification with user data."""
        notification = self.repository.get_with_user(db, id)
        if not notification:
            raise NotFoundError(detail="Notification not found")
        return notification
    
    def create_notification(
        self, db: Session, *, obj_in: NotificationCreate, send_email: bool = False
    ) -> Notification:
        """Create a new notification with optional email."""
        # Create notification in database
        notification = self.repository.create(db, obj_in=obj_in)
        
        # Send email if requested
        if send_email and notification.user.email:
            self.email_service.send_notification_email(
                email_to=notification.user.email,
                subject=notification.title,
                body=notification.message
            )
        
        return notification
    
    def mark_as_read(self, db: Session, *, id: int) -> Notification:
        """Mark a notification as read."""
        notification = self.repository.get(db, id)
        if not notification:
            raise NotFoundError(detail="Notification not found")
        
        return self.repository.mark_as_read(db, db_obj=notification)
    
    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        """Mark all notifications for a user as read."""
        return self.repository.mark_all_as_read(db, user_id=user_id)
    
    def get_user_notifications(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100, unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        if unread_only:
            return self.repository.get_unread_by_user(db, user_id=user_id, skip=skip, limit=limit)
        return self.repository.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def count_unread(self, db: Session, *, user_id: int) -> int:
        """Count unread notifications for a user."""
        return self.repository.count_unread_by_user(db, user_id=user_id)
    
    def get_filtered_notifications(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Notification]:
        """Get notifications with filtering."""
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)
    
    def create_system_notification(
        self, db: Session, *, user_id: int, title: str, message: str, 
        send_email: bool = False, entity_id: Optional[int] = None, 
        entity_type: Optional[str] = None
    ) -> Notification:
        """Create a system notification."""
        notification_data = NotificationCreate(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType.SYSTEM,
            entity_id=entity_id,
            entity_type=entity_type,
            is_read=False
        )
        
        return self.create_notification(db, obj_in=notification_data, send_email=send_email)