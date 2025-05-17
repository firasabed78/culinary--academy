from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.domain.models.notification import NotificationType


class NotificationBase(BaseModel):
    """Base schema for notification data."""
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    notification_type: NotificationType
    entity_id: Optional[int] = None
    entity_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a new notification."""
    is_read: bool = False


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    is_read: Optional[bool] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    message: Optional[str] = Field(None, min_length=1)


class NotificationInDB(NotificationBase):
    """Schema for notification in database."""
    id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Notification(NotificationInDB):
    """Schema for notification API response."""
    pass


class NotificationWithUser(Notification):
    """Schema for notification with user details."""
    from app.domain.schemas.user import User

    user: User