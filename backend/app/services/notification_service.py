"""
notification_service.py - Service layer for notification management
This file handles business logic related to user notifications, including
sending, updating, filtering, and email dispatch features. It provides 
an abstraction over the notification repository and integrates with 
the email service.
"""
"""
notification_service.py - Service layer for notification management
This file handles business logic related to user notifications, including
sending, updating, filtering, and email dispatch features. It provides 
an abstraction over the notification CRUD and integrates with 
the email service.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.models.notification import Notification, NotificationType
from app.domain.schemas.notification import NotificationCreate, NotificationUpdate
from app.crud import notification as crud_notification
from app.crud import user as crud_user
from app.core.exceptions import NotFoundError
from app.services.email_service import EmailService


class NotificationService:
    """Service for notification operations using CRUD abstractions."""
    
    def __init__(self):
        # Create an instance of email service for sending notification emails
        self.email_service = EmailService()
    
    def get(self, db: Session, id: int) -> Optional[Notification]:
        """
        Get a notification by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Notification ID
        
        Returns
        -------
        Optional[Notification]
            Notification if found, None otherwise
        """
        return crud_notification.get(db, id)
    
    def get_with_user(self, db: Session, id: int) -> Optional[Notification]:
        """
        Get a notification with user data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Notification ID
        
        Returns
        -------
        Optional[Notification]
            Notification with user data if found
            
        Raises
        ------
        NotFoundError
            If notification not found
        """
        notification = crud_notification.get_with_user(db, id)
        if not notification:
            raise NotFoundError(detail="Notification not found")
        return notification
    
    def create_notification(
        self, db: Session, *, obj_in: NotificationCreate, send_email: bool = False
    ) -> Notification:
        """
        Create a new notification with optional email.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Notification creation data
        send_email: Whether to send email notification
        
        Returns
        -------
        Notification
            Created notification instance
        """
        # Create notification in database using CRUD
        notification = crud_notification.create(db, obj_in=obj_in)
        
        # Send email if requested and user has email
        if send_email and notification.user.email:
            self.email_service.send_notification_email(
                email_to=notification.user.email,
                subject=notification.title,
                body=notification.message
            )
        
        return notification
    
    def mark_as_read(self, db: Session, *, id: int) -> Notification:
        """
        Mark a notification as read.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Notification ID
        
        Returns
        -------
        Notification
            Updated notification instance
            
        Raises
        ------
        NotFoundError
            If notification not found
        """
        notification = crud_notification.get(db, id)
        if not notification:
            raise NotFoundError(detail="Notification not found")
        return crud_notification.mark_as_read(db, db_obj=notification)
    
    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        """
        Mark all notifications for a user as read.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        
        Returns
        -------
        int
            Number of notifications marked as read
        """
        return crud_notification.mark_all_as_read(db, user_id=user_id)
    
    def get_user_notifications(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100, unread_only: bool = False
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        unread_only: If True, only return unread notifications
        
        Returns
        -------
        List[Notification]
            List of user notifications
        """
        if unread_only:
            return crud_notification.get_unread_by_user(db, user_id=user_id, skip=skip, limit=limit)
        return crud_notification.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def count_unread(self, db: Session, *, user_id: int) -> int:
        """
        Count unread notifications for a user.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        
        Returns
        -------
        int
            Number of unread notifications
        """
        return crud_notification.count_unread_by_user(db, user_id=user_id)
    
    def get_filtered_notifications(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Notification]:
        """
        Get notifications with filtering.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        **filters: Additional filters to apply
        
        Returns
        -------
        List[Notification]
            List of filtered notifications
        """
        return crud_notification.get_multi_by_filters(db, skip=skip, limit=limit, **filters)
    
    def create_system_notification(
        self, db: Session, *, user_id: int, title: str, message: str,
        send_email: bool = False, entity_id: Optional[int] = None,
        entity_type: Optional[str] = None
    ) -> Notification:
        """
        Create a system notification.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to notify
        title: Notification title
        message: Notification message
        send_email: Whether to send email notification
        entity_id: Related entity ID
        entity_type: Related entity type
        
        Returns
        -------
        Notification
            Created notification instance
        """
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