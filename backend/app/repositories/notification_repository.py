from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.domain.models.notification import Notification, NotificationType
from app.domain.schemas.notification import NotificationCreate, NotificationUpdate
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """Repository for notification operations."""
    
    def __init__(self):
        super().__init__(Notification)

    def get_with_user(self, db: Session, id: int) -> Optional[Notification]:
        """Get a notification with related user data."""
        return db.query(self.model)\
            .options(joinedload(self.model.user))\
            .filter(self.model.id == id)\
            .first()

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """Get all notifications for a user."""
        return db.query(self.model)\
            .filter(self.model.user_id == user_id)\
            .order_by(self.model.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_unread_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """Get unread notifications for a user."""
        return db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False
            )\
            .order_by(self.model.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_type(
        self, db: Session, *, notification_type: NotificationType, skip: int = 0, limit: int = 100
    ) -> List[Notification]:
        """Get notifications by type."""
        return db.query(self.model)\
            .filter(self.model.notification_type == notification_type)\
            .order_by(self.model.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    def mark_as_read(self, db: Session, *, db_obj: Notification) -> Notification:
        """Mark a notification as read."""
        db_obj.is_read = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def mark_all_as_read(self, db: Session, *, user_id: int) -> int:
        """Mark all notifications for a user as read."""
        count = db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False
            )\
            .update({"is_read": True})
        db.commit()
        return count

    def count_unread_by_user(self, db: Session, *, user_id: int) -> int:
        """Count unread notifications for a user."""
        return db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.is_read == False
            )\
            .count()

    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Notification]:
        """Get notifications with complex filtering."""
        query = db.query(self.model)
        
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
                search_term = f"%{value}%"
                query = query.filter(
                    self.model.title.ilike(search_term) | 
                    self.model.message.ilike(search_term)
                )
        
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()