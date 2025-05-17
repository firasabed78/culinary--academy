"""
Objective: Implement user management endpoints.
This file defines the API endpoints for creating, retrieving, updating,
and deleting user accounts, with appropriate access control.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.domain.models.user import User
from app.domain.schemas.user import (
    User as UserSchema, UserCreate, UserUpdate, UserWithEnrollments
)
from app.services.user_service import UserService
from app.core.exceptions import NotFoundError, ValidationError

# Create a router for user endpoints
router = APIRouter()

# Create a service instance for user operations
user_service = UserService()

@router.get("/", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    role: Optional[str] = None,  # Filter by role
    is_active: Optional[bool] = None,  # Filter by active status
    search: Optional[str] = None,  # Search by name/email
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Retrieve users with filtering.
    
    This endpoint returns a list of users with optional filtering by role,
    active status, and search term. Admin access only.
    """
    # Build filters
    filters = {}
    if role:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    if search:
        filters["search"] = search
    
    return user_service.get_filtered_users(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=UserSchema)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,  # User data
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Create new user.
    
    This endpoint creates a new user with the provided information.
    Admin access only.
    """
    try:
        # Check if email already exists
        user = user_service.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        return user_service.create_user(db, obj_in=user_in)
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get current user.
    
    This endpoint returns the authenticated user's profile information.
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,  # Update data
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Update current user.
    
    This endpoint allows users to update their own profile information.
    """
    try:
        # Users cannot change their own role
        if user_in.role and user_in.role != current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role"
            )
        
        # Update user
        return user_service.update(db, db_obj=current_user, obj_in=user_in)
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=UserWithEnrollments)
def read_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # User ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get user by ID with enrollments.
    
    This endpoint returns a user's profile with their enrollments.
    Users can only view their own profile, while admins can view any user.
    """
    try:
        # Check permissions - users can only view their own profile
        if current_user.role != "admin" and current_user.id != id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this user"
            )
        
        # Get user with enrollments
        user = user_service.get_with_enrollments(db, id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/{id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # User ID
    user_in: UserUpdate,  # Update data
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Update user.
    
    This endpoint allows admins to update any user's profile.
    """
    try:
        # Get user
        user = user_service.get(db, id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Update user
        return user_service.update(db, db_obj=user, obj_in=user_in)
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{id}", response_model=UserSchema)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # User ID
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Delete user.
    
    This endpoint allows admins to delete users.
    Users cannot be permanently deleted, only deactivated.
    """
    try:
        # Get user
        user = user_service.get(db, id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        # Prevent deleting the last admin
        if user.role == "admin":
            admin_count = user_service.count_admins(db)
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )
        
        # Soft delete user
        return user_service.deactivate_user(db, id=id)
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/{id}/activate", response_model=UserSchema)
def activate_user(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # User ID
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Activate user.
    
    This endpoint allows admins to activate a deactivated user.
    """
    try:
        # Activate user
        return user_service.activate_user(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )