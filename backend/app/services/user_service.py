"""
user_service.py - Service layer for user management and authentication
This file handles business logic related to user operations, including 
user creation, authentication, password management, and user statistics.
It enforces validation rules such as preventing duplicate emails and
provides token-based authentication functionality.
"""

from typing import Optional, List, Dict, Any  # Import type hints for function signatures
from sqlalchemy.orm import Session  # Import SQLAlchemy session for database operations
from datetime import timedelta  # Import timedelta for token expiration time

from app.domain.models.user import User  # Import User model
from app.domain.schemas.user import UserCreate, UserUpdate, UserWithToken  # Import User schemas
from app.repositories.user_repository import UserRepository  # Import repository for user DB operations
from app.services.base import BaseService  # Import base service with common CRUD operations
from app.core.security import create_access_token  # Import token generation function
from app.core.config import settings  # Import application settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError  # Import custom exceptions

class UserService(BaseService[User, UserCreate, UserUpdate, UserRepository]):
    """Service for user operations."""
    
    def __init__(self):
        # Initialize with user repository
        super().__init__(UserRepository)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email."""
        # Delegate to repository to find user by email
        return self.repository.get_by_email(db, email=email)
    
    def create_user(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with duplicate email check."""
        # Check if user with this email already exists
        user = self.get_by_email(db, email=obj_in.email)
        if user:
            # Prevent duplicate email registration
            raise ValidationError(detail="User with this email already exists")
        # Create user if email is unique
        return self.repository.create(db, obj_in=obj_in)
    
    def authenticate(self, db: Session, *, email: str, password: str) -> UserWithToken:
        """Authenticate a user and return user with access token."""
        # Attempt to authenticate user with credentials
        user = self.repository.authenticate(db, email=email, password=password)
        if not user:
            # Invalid credentials
            raise AuthenticationError(detail="Incorrect email or password")
        
        # Check if user account is active
        if not self.repository.is_active(user):
            # Prevent inactive users from logging in
            raise AuthenticationError(detail="Inactive user")
        
        # Generate access token with configured expiration time
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id, expires_delta=access_token_expires
        )
        
        # Return user data with token for client authentication
        return UserWithToken(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            access_token=access_token,
            token_type="bearer"  # Token type for Authorization header
        )
    
    def update_user(self, db: Session, *, id: int, obj_in: UserUpdate) -> User:
        """Update user with existence check."""
        # Verify user exists before updating
        user = self.get(db, id)
        if not user:
            raise NotFoundError(detail="User not found")
        # Update user details
        return self.update(db, id=id, obj_in=obj_in)
    
    def update_password(self, db: Session, *, user_id: int, new_password: str) -> User:
        """Update user password."""
        # Find user by ID
        user = self.get(db, user_id)
        if not user:
            raise NotFoundError(detail="User not found")
        # Update user password with hashing handled by repository
        return self.repository.update_password(db, user=user, new_password=new_password)
    
    def get_user_stats(self, db: Session) -> Dict[str, Any]:
        """Get user statistics."""
        # Count total users
        total = db.query(User).count()
        # Count users by role
        students = db.query(User).filter(User.role == "student").count()
        instructors = db.query(User).filter(User.role == "instructor").count()
        admins = db.query(User).filter(User.role == "admin").count()
        
        # Return statistics dictionary
        return {
            "total": total,
            "students": students,
            "instructors": instructors,
            "admins": admins
        }