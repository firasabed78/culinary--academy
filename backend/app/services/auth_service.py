"""
auth_service.py - Service layer for authentication operations
This file handles authentication-related business logic including login,
token generation, password reset, and user verification operations.
"""

from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy.orm import Session

from app.domain.models.user import User
from app.domain.schemas.user import UserWithToken
from app.crud import user as crud_user
from app.core.security import create_access_token, verify_password
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.services.email_service import EmailService


class AuthService:
    """Service for authentication operations using CRUD abstractions."""
    
    def __init__(self):
        """Initialize auth service with email service."""
        self.email_service = EmailService()
    
    def authenticate_user(
        self, db: Session, *, email: str, password: str
    ) -> UserWithToken:
        """
        Authenticate a user and return user with access token.
        
        Parameters
        ----------
        db: SQLAlchemy session
        email: User's email address
        password: User's password
        
        Returns
        -------
        UserWithToken
            Authenticated user with access token
            
        Raises
        ------
        AuthenticationError
            If authentication fails or user is inactive
        """
        # Authenticate user credentials
        user = crud_user.authenticate(db, email=email, password=password)
        if not user:
            raise AuthenticationError(detail="Incorrect email or password")
        
        # Check if user is active
        if not crud_user.is_active(user):
            raise AuthenticationError(detail="Account is deactivated")
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        # Return user with token
        return UserWithToken(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            access_token=access_token,
            token_type="bearer"
        )
    
    def get_current_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """
        Get current user by ID (from token).
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID from JWT token
        
        Returns
        -------
        Optional[User]
            Current user if found and active, None otherwise
            
        Raises
        ------
        AuthenticationError
            If user not found or inactive
        """
        user = crud_user.get(db, user_id)
        if not user:
            raise AuthenticationError(detail="User not found")
        
        if not crud_user.is_active(user):
            raise AuthenticationError(detail="Account is deactivated")
        
        return user
    
    def verify_user_permissions(
        self, db: Session, *, user_id: int, required_role: str = None
    ) -> bool:
        """
        Verify user permissions for an action.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to check
        required_role: Required role ("admin", "instructor", "student")
        
        Returns
        -------
        bool
            True if user has required permissions, False otherwise
        """
        user = crud_user.get(db, user_id)
        if not user or not crud_user.is_active(user):
            return False
        
        if required_role:
            if required_role == "admin" and not crud_user.is_admin(user):
                return False
            elif required_role == "instructor" and not crud_user.is_instructor(user):
                return False
            # Note: All users can have "student" level access
        
        return True
    
    def change_password(
        self, db: Session, *, user_id: int, current_password: str, new_password: str
    ) -> bool:
        """
        Change user password.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        current_password: Current password
        new_password: New password
        
        Returns
        -------
        bool
            True if password changed successfully, False otherwise
            
        Raises
        ------
        AuthenticationError
            If current password is incorrect or user not found
        """
        user = crud_user.get(db, user_id)
        if not user:
            raise AuthenticationError(detail="User not found")
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError(detail="Current password is incorrect")
        
        # Update password
        crud_user.update(db, db_obj=user, obj_in={"password": new_password})
        
        # Send confirmation email
        self.email_service.send_notification_email(
            email_to=user.email,
            subject="Password Changed Successfully",
            body="Your password has been changed successfully. If you did not make this change, please contact support immediately."
        )
        
        return True
    
    def initiate_password_reset(self, db: Session, *, email: str) -> bool:
        """
        Initiate password reset process.
        
        Parameters
        ----------
        db: SQLAlchemy session
        email: User's email address
        
        Returns
        -------
        bool
            True if reset email sent, False if user not found
        """
        user = crud_user.get_by_email(db, email=email)
        if not user:
            # For security, don't reveal if email exists
            return True
        
        if not crud_user.is_active(user):
            return True
        
        # Generate reset token (simplified - in production, use a secure token)
        reset_token = create_access_token(
            subject=user.id, 
            expires_delta=timedelta(hours=1)  # 1 hour expiry
        )
        
        # Send reset email
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        self.email_service.send_notification_email(
            email_to=user.email,
            subject="Password Reset Request",
            body=f"""
            <p>You have requested a password reset for your Culinary Academy account.</p>
            <p>Click the link below to reset your password:</p>
            <p><a href="{reset_link}">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this reset, please ignore this email.</p>
            """
        )
        
        return True
    
    def reset_password_with_token(
        self, db: Session, *, token: str, new_password: str
    ) -> bool:
        """
        Reset password using reset token.
        
        Parameters
        ----------
        db: SQLAlchemy session
        token: Password reset token
        new_password: New password
        
        Returns
        -------
        bool
            True if password reset successfully, False otherwise
            
        Raises
        ------
        AuthenticationError
            If token is invalid or expired
        """
        try:
            # Decode token to get user ID
            # This would normally use JWT decode with proper verification
            from app.core.security import decode_access_token
            user_id = decode_access_token(token)
            
            if not user_id:
                raise AuthenticationError(detail="Invalid reset token")
            
            # Get user
            user = crud_user.get(db, user_id)
            if not user:
                raise AuthenticationError(detail="User not found")
            
            # Update password
            crud_user.update(db, db_obj=user, obj_in={"password": new_password})
            
            # Send confirmation email
            self.email_service.send_notification_email(
                email_to=user.email,
                subject="Password Reset Successful",
                body="Your password has been reset successfully. You can now log in with your new password."
            )
            
            return True
            
        except Exception as e:
            raise AuthenticationError(detail="Invalid or expired reset token")
    
    def logout_user(self, db: Session, *, user_id: int) -> bool:
        """
        Logout user (in this implementation, just verify user exists).
        
        Note: In a stateless JWT implementation, logout is handled client-side
        by removing the token. For enhanced security, you might implement
        token blacklisting or short-lived refresh tokens.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        
        Returns
        -------
        bool
            True if logout successful
        """
        user = crud_user.get(db, user_id)
        if not user:
            return False
        
        # In a more sophisticated implementation, you might:
        # - Add token to blacklist
        # - Revoke refresh tokens
        # - Log the logout event
        
        return True
    
    def refresh_token(self, db: Session, *, user_id: int) -> UserWithToken:
        """
        Refresh user access token.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID from refresh token
        
        Returns
        -------
        UserWithToken
            User with new access token
            
        Raises
        ------
        AuthenticationError
            If user not found or inactive
        """
        user = crud_user.get(db, user_id)
        if not user:
            raise AuthenticationError(detail="User not found")
        
        if not crud_user.is_active(user):
            raise AuthenticationError(detail="Account is deactivated")
        
        # Generate new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        return UserWithToken(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            access_token=access_token,
            token_type="bearer"
        )
    
    def validate_admin_access(self, db: Session, *, user_id: int) -> bool:
        """
        Validate that user has admin access.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to check
        
        Returns
        -------
        bool
            True if user is admin, False otherwise
        """
        user = crud_user.get(db, user_id)
        if not user or not crud_user.is_active(user):
            return False
        
        return crud_user.is_admin(user)
    
    def validate_instructor_access(self, db: Session, *, user_id: int) -> bool:
        """
        Validate that user has instructor access.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to check
        
        Returns
        -------
        bool
            True if user is instructor or admin, False otherwise
        """
        user = crud_user.get(db, user_id)
        if not user or not crud_user.is_active(user):
            return False
        
        return crud_user.is_instructor(user) or crud_user.is_admin(user)
    
    def deactivate_user_account(self, db: Session, *, user_id: int, admin_id: int) -> bool:
        """
        Deactivate a user account (admin only).
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to deactivate
        admin_id: Admin user ID performing the action
        
        Returns
        -------
        bool
            True if account deactivated successfully
            
        Raises
        ------
        AuthenticationError
            If admin permissions invalid or user not found
        """
        # Verify admin permissions
        if not self.validate_admin_access(db, user_id=admin_id):
            raise AuthenticationError(detail="Admin access required")
        
        # Get target user
        user = crud_user.get(db, user_id)
        if not user:
            raise AuthenticationError(detail="User not found")
        
        # Deactivate account
        crud_user.update(db, db_obj=user, obj_in={"is_active": False})
        
        # Send notification email
        self.email_service.send_notification_email(
            email_to=user.email,
            subject="Account Deactivated",
            body="Your account has been deactivated. If you believe this is an error, please contact support."
        )
        
        return True
    
    def reactivate_user_account(self, db: Session, *, user_id: int, admin_id: int) -> bool:
        """
        Reactivate a user account (admin only).
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID to reactivate
        admin_id: Admin user ID performing the action
        
        Returns
        -------
        bool
            True if account reactivated successfully
            
        Raises
        ------
        AuthenticationError
            If admin permissions invalid or user not found
        """
        # Verify admin permissions
        if not self.validate_admin_access(db, user_id=admin_id):
            raise AuthenticationError(detail="Admin access required")
        
        # Get target user
        user = crud_user.get(db, user_id)
        if not user:
            raise AuthenticationError(detail="User not found")
        
        # Reactivate account
        crud_user.update(db, db_obj=user, obj_in={"is_active": True})
        
        # Send notification email
        self.email_service.send_notification_email(
            email_to=user.email,
            subject="Account Reactivated",
            body="Your account has been reactivated. You can now log in and access all features."
        )
        
        return True