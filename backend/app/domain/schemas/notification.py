"""
Objective: Define data validation and serialization models for notification resources.
This file defines the Pydantic models used for validating notification-related data
in requests and responses, ensuring type safety and data integrity.

These schema files define the data validation and serialization models used throughout the application. Key features include:

Type Safety: Using Python type hints and Pydantic's validation system to ensure data integrity.
Validation Rules: Fields have constraints like minimum/maximum lengths and custom validators.
Schema Organization:

Base models define common fields shared across schemas
Create models extend base models with fields needed for creation
Update models contain optional fields for partial updates
InDB models represent complete database records including auto-generated fields
Response models define what's returned in API responses


Circular Import Handling: Imports that would cause circular dependencies are done within class definitions rather than at the module level.
ORM Integration: orm_mode = True enables seamless conversion between SQLAlchemy models and Pydantic schemas.
Related Data Models: Extended schemas like WithUser or WithDetails include related entity data for comprehensive API responses.

This approach ensures consistent data validation, clear API contracts, and a clean separation between database models and API representations, all while maintaining type safety throughout the application.

"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from app.domain.models.notification import NotificationType  # Import enum from SQLAlchemy model

class NotificationBase(BaseModel):
    """
    Base schema for notification data.
    
    Contains common fields that are shared across all notification schemas,
    serving as the foundation for more specific notification models.
    """
    user_id: int  # The user receiving the notification
    title: str = Field(..., min_length=1, max_length=255)  # Required non-empty title with max length
    message: str = Field(..., min_length=1)  # Required non-empty message
    notification_type: NotificationType  # The type of notification (enum)
    entity_id: Optional[int] = None  # Optional ID of related entity (course, enrollment, etc.)
    entity_type: Optional[str] = None  # Optional type of related entity

class NotificationCreate(NotificationBase):
    """
    Schema for creating a new notification.
    
    Extends the base schema with additional fields required when creating
    a new notification, including the default read status.
    """
    is_read: bool = False  # Default to unread

class NotificationUpdate(BaseModel):
    """
    Schema for updating a notification.
    
    Contains fields that can be updated after notification creation.
    All fields are optional as updates may only change specific fields.
    """
    is_read: Optional[bool] = None  # Update read status
    title: Optional[str] = Field(None, min_length=1, max_length=255)  # Update title
    message: Optional[str] = Field(None, min_length=1)  # Update message

class NotificationInDB(NotificationBase):
    """
    Schema for notification in database.
    
    Complete notification model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    is_read: bool  # Whether the notification has been read
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Notification(NotificationInDB):
    """
    Schema for notification API response.
    
    The primary model used for API responses containing notification data.
    Inherits all fields from NotificationInDB.
    """
    pass

class NotificationWithUser(Notification):
    """
    Schema for notification with user details.
    
    Extended notification model that includes the associated user's information,
    typically used for detailed notification views.
    """
    from app.domain.schemas.user import User  # Import needed here to avoid circular imports
    user: User  # The user receiving the notification