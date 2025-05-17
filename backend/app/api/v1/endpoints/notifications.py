from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.domain.models.user import User
from app.domain.models.notification import NotificationType
from app.domain.schemas.notification import (
    Notification, NotificationCreate, NotificationUpdate, NotificationWithUser
)
from app.services.notification_service import NotificationService
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
notification_service = NotificationService()

@router.get("/", response_model=List[Notification])
def read_notifications(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve user's notifications with filtering.
    """
    # Build filters
    filters = {
        "user_id": current_user.id
    }
    
    if is_read is not None:
        filters["is_read"] = is_read
    
    if notification_type:
        filters["notification_type"] = notification_type
    
    return notification_service.get_filtered_notifications(
        db, skip=skip, limit=limit, **filters
    )

@router.get("/unread-count", response_model=dict)
def count_unread_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Count unread notifications for the current user.
    """
    count = notification_service.count_unread(db, user_id=current_user.id)
    return {"count": count}

@router.post("/", response_model=Notification)
def create_notification(
    *,
    db: Session = Depends(deps.get_db),
    notification_in: NotificationCreate,
    send_email: bool = False,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Create a new notification (admin only).
    """
    try:
        return notification_service.create_notification(
            db, obj_in=notification_in, send_email=send_email
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=NotificationWithUser)
def read_notification(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get notification by ID with user details.
    """
    try:
        notification = notification_service.get_with_user(db, id)
        
        # Check permissions
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this notification"
            )
        
        return notification
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}/read", response_model=Notification)
def mark_notification_as_read(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mark a notification as read.
    """
    try:
        notification = notification_service.get(db, id)
        
        # Check permissions
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this notification"
            )
        
        return notification_service.mark_as_read(db, id=id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Mark all notifications for the current user as read.
    """
    count = notification_service.mark_all_as_read(db, user_id=current_user.id)
    return {"count": count}

@router.delete("/{id}", response_model=Notification)
def delete_notification(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a notification.
    """
    try:
        notification = notification_service.get(db, id)
        
        # Check permissions
        if current_user.role != "admin" and notification.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this notification"
            )
        
        return notification_service.remove(db, id=id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/", response_model=dict)
def delete_all_notifications(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete all notifications for the current user.
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )