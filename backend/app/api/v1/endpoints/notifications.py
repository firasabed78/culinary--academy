"""
Objective: Implement notification management endpoints.
This file defines the API endpoints for creating, retrieving, updating,
and deleting notifications, with proper access control and filtering.

This file implements a comprehensive notification management API:

Purpose: Provides a complete interface for managing user notifications, including creation, retrieval, marking as read, and deletion.
Key Endpoints:

GET /: List user notifications with filtering
GET /unread-count: Count unread notifications (for badges/indicators)
POST /: Create new notifications (admin only)
GET /{id}: Get a specific notification's details
PUT /{id}/read: Mark a notification as read
PUT /read-all: Mark all notifications as read
DELETE /{id}: Delete a notification
DELETE /: Delete all notifications


Design Patterns:

User-Specific Data Access: Each user can only see and manage their own notifications
Batch Operations: Endpoints for managing all notifications at once
Admin Override: Admins can access and manage any notification
Read Tracking: Specific endpoints for read status management


Security Features:

Authentication for all endpoints
Authorization checks for each operation
Data isolation between users


Notable Implementation Details:

Unread count feature for notification badges in UI
Batch operations for convenience
Optional email integration for important notifications
Comprehensive filtering options


Improvement Ideas:

The delete_all_notifications endpoint could be optimized by using a bulk delete operation in the service layer rather than deleting each notification individually
Consider adding a "mark-all-as-read-by-type" endpoint for more granular control



This API provides a solid foundation for implementing a notification system that can be used for real-time updates, system alerts, and user-to-user communications within the application.

"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps  # Authentication dependencies
from app.domain.models.user import User
from app.domain.models.notification import NotificationType  # Notification type enum
from app.domain.schemas.notification import (
    Notification, NotificationCreate, NotificationUpdate, NotificationWithUser  # Data models/schemas
)
from app.services.notification_service import NotificationService  # Notification business logic
from app.core.exceptions import NotFoundError, ValidationError  # Custom exceptions

# Create a router for notification endpoints
router = APIRouter()

# Create a service instance for notification operations
notification_service = NotificationService()

@router.get("/", response_model=List[Notification])
def read_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    is_read: Optional[bool] = None,  # Filter by read status
    notification_type: Optional[NotificationType] = None,  # Filter by notification type
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Retrieve user's notifications with filtering.
    
    This endpoint returns the current user's notifications with optional
    filtering by read status and notification type.
    """
    # Build filters - always filter by current user's ID
    filters = {
        "user_id": current_user.id
    }
    
    # Add optional filters
    if is_read is not None:
        filters["is_read"] = is_read
    
    if notification_type:
        filters["notification_type"] = notification_type
    
    # Get filtered notifications
    return notification_service.get_filtered_notifications(
        db, skip=skip, limit=limit, **filters
    )

@router.get("/unread-count", response_model=dict)
def count_unread_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Count unread notifications for the current user.
    
    This endpoint returns the number of unread notifications for the
    authenticated user, typically used for notification badges.
    """
    count = notification_service.count_unread(db, user_id=current_user.id)
    return {"count": count}

@router.post("/", response_model=Notification)
def create_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: NotificationCreate,  # Notification data
    send_email: bool = False,  # Optional email sending flag
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Create a new notification (admin only).
    
    This endpoint allows administrators to manually create notifications
    for users, with an option to send an email notification as well.
    """
    try:
        # Create notification using service
        return notification_service.create_notification(
            db, obj_in=notification_in, send_email=send_email
        )
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=NotificationWithUser)
def read_notification(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Notification ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get notification by ID with user details.
    
    This endpoint returns a single notification with its associated user,
    ensuring the requester has permission to view it.
    """
    try:
        # Get notification with user details
        notification = notification_service.get_with_user(db, id)
        
        # Check permissions - only admins or the notification recipient can view
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this notification"
            )
        
        return notification
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}/read", response_model=Notification)
def mark_notification_as_read(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Notification ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Mark a notification as read.
    
    This endpoint marks a specific notification as read,
    ensuring the requester has permission to update it.
    """
    try:
        # Get notification to check permissions
        notification = notification_service.get(db, id)
        
        # Check permissions - only admins or the notification recipient can update
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this notification"
            )
        
        # Mark notification as read
        return notification_service.mark_as_read(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Mark all notifications for the current user as read.
    
    This endpoint marks all of the authenticated user's notifications as read
    and returns the count of updated notifications.
    """
    count = notification_service.mark_all_as_read(db, user_id=current_user.id)
    return {"count": count}

@router.delete("/{id}", response_model=Notification)
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Notification ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Delete a notification.
    
    This endpoint deletes a specific notification,
    ensuring the requester has permission to delete it.
    """
    try:
        # Get notification to check permissions
        notification = notification_service.get(db, id)
        
        # Check permissions - only admins or the notification recipient can delete
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this notification"
            )
        
        # Delete notification
        return notification_service.remove(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/", response_model=dict)
def delete_all_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Delete all notifications for the current user.
    
    This endpoint deletes all of the authenticated user's notifications
    and returns the count of deleted notifications.
    """
    try:
        # Get all user's notifications
        filters = {"user_id": current_user.id}
        notifications = notification_service.get_filtered_notifications(db, **filters)
        
        # Delete each notification
        count = 0
        for notification in notifications:
            notification_service.remove(db, id=notification.id)
            count += 1
        
        return {"count": count}
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )