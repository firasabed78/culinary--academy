"""
Objective: Implement a specialized repository for notification operations.
This file extends the base repository with notification-specific query methods,
providing functionality for managing user notifications and their read status.

The NotificationRepository focuses on managing the notification system of your application, providing methods to handle the full lifecycle of user notifications.
Key Features:

Notification Management:

User Notifications: Retrieving notifications for specific users
Read Status: Tracking and updating the read/unread status
Notification Types: Filtering by different notification categories
Entity Relationship: Support for notifications linked to specific entities


Specialized Operations:

Mark as Read: Methods for marking individual or all notifications as read
Unread Counts: Counting unread notifications for UI badges
Time-Ordered Results: Consistent ordering by creation date, newest first
Text Search: Finding notifications by title or message content


Bulk Operations:

Bulk Status Update: Efficient mass-update of notification status
Status Tracking: Simple APIs for changing notification read status


Data Access Patterns:

User-Centric Access: Methods optimized for retrieving a user's notifications
Entity-based Filtering: Finding notifications related to specific entities
Type-based Filtering: Categorizing notifications by type



The repository includes a comprehensive set of methods for working with notifications, with particular attention to the common use cases in a notification system:

Viewing notifications: Methods to retrieve a user's notifications with various filters
Marking notifications as read: Both individual and bulk operations
Counting unread notifications: For notification badges and indicators
Filtering by type or content: For organizing and searching notifications

The consistent ordering by creation date (newest first) reflects the typical user expectation for notification feeds, and the comprehensive set of filter options supports both user-facing interfaces and administrative dashboards.
This repository plays a key role in the application's communication and alert system, enabling timely updates to users about important events like enrollment status changes, payment confirmations, and system notifications.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships

from app.domain.models.notification import Notification, NotificationType
from app.domain.schemas.notification import NotificationCreate, NotificationUpdate
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """
    Repository for notification operations.
    
    Extends the base repository with notification-specific queries for
    retrieving, filtering, and updating user notifications.
    """
    
    def __init__(self):
        """Initialize with Notification model."""
        super().__init__(Notification)

    def get_with_user(self, db: Session, id: int) -> Optional[Notification]:
        """
        Get a notification with related user data.
        
        Uses eager loading to retrieve a notification with its associated user
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Notification ID
            
        Returns:
            Notification with loaded user relationship or None if not found
        """
        return db.query(self.model)\
            .options(joinedload(self.model.user))\
            .filter(self.model.id == id)\
            .first()

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """
        Get all notifications for a user.
        
        Retrieves all notifications for a specific user, ordered by creation date
        with newest first, and with pagination.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of notifications for the user, ordered by creation date (newest first)
        """
        return db.query(self.model)\
            .filter(self.model.user_id == user_id)\
            .order_by(self.model.created_at.desc())  # Newest first
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_unread_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """
        Get unread notifications for a user.
        
        Retrieves only unread notifications for a specific user, ordered by
        creation date with newest first, and with pagination.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of unread notifications for the user, ordered by creation date
        """
        return db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False  # Only unread
            )\
            .order_by(self.model.created_at.desc())  # Newest first
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_type(
        self, db: Session, *, notification_type: NotificationType, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """
        Get notifications by type.
        
        Retrieves notifications of a specific type (e.g., system, course),
        ordered by creation date with newest first, and with pagination.
        
        Args:
            db: SQLAlchemy database session
            notification_type: NotificationType enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of notifications of the specified type, ordered by creation date
        """
        return db.query(self.model)\
            .filter(self.model.notification_type == notification_type)\
            .order_by(self.model.created_at.desc())  # Newest first
            .offset(skip)\
            .limit(limit)\
            .all()

    def mark_as_read(self, db: Session, *, db_obj: Notification) -> Notification:
        """
        Mark a notification as read.
        
        Updates a specific notification's read status to 'read'
        and persists the change to the database.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Notification object to update
            
        Returns:
            Updated notification object
        """
        db_obj.is_read = True  # Mark as read
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get updated values
        return db_obj

    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        """
        Mark all notifications for a user as read.
        
        Updates all unread notifications for a specific user to 'read' status.
        Uses a bulk update for efficiency.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID whose notifications to update
            
        Returns:
            Number of notifications marked as read
        """
        # Bulk update with count of affected rows
        count = db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False
            )\
            .update({"is_read": True})
        db.commit()  # Commit transaction
        return count  # Return count of updated rows

    def count_unread_by_user(self, db: Session, *, user_id: int) -> int:
        """
        Count unread notifications for a user.
        
        Gets the count of unread notifications for a specific user,
        useful for notification badges in the UI.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID to count notifications for
            
        Returns:
            Count of unread notifications for the user
        """
        return db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False
            )\
            .count()

    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Notification]:
        """
        Get notifications with complex filtering.
        
        Applies multiple filtering conditions based on the provided
        filter parameters, supporting a wide range of query criteria.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Field name/value pairs for filtering
            
        Returns:
            List of notifications matching the filter criteria,
            ordered by creation date (newest first)
        """
        query = db.query(self.model)
        
        # Apply filters based on filter name and value
        for key, value in filters.items():
            if key == "user_id" and value:
                query = query.filter(self.model.user_id == value)
            elif key == "is_read" and value is not None:
                query = query.filter(self.model.is_read == value)
            elif key == "notification_type" and value:
                query = query.filter(self.model.notification_type == value)
            elif key == "entity_id" and value:
                query = query.filter(self.model.entity_id == value)
            elif key == "entity_type" and value:
                query = query.filter(self.model.entity_type == value)
            elif key == "search" and value:
                # Search in title and message
                search_term = f"%{value}%"
                query = query.filter(
                    self.model.title.ilike(search_term) | 
                    self.model.message.ilike(search_term)
                )
        
        # Always order by creation date, newest first
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()