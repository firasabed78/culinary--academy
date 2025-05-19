"""
user_service.py - Service layer for user management
This file provides business logic operations for users in the Culinary Academy
Student Registration system, including authentication, registration, and profile
management functionality.
"""
"""
user_service.py - Service layer for user management
This file provides business logic operations for users in the Culinary Academy
Student Registration system, including authentication, registration, and profile
management functionality.
"""

from typing import Optional, List, Dict, Any
from datetime import timedelta
from sqlalchemy.orm import Session

from app.domain.models.user import User
from app.domain.schemas.user import UserCreate, UserUpdate, UserWithToken
from app.crud import user as crud_user
from app.core.security import create_access_token
from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError


class UserService:
    """Service for user operations using CRUD abstractions."""
    
    def get(self, db: Session, id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: User ID to retrieve
        
        Returns
        -------
        Optional[User]
            User if found, None otherwise
        """
        return crud_user.get(db, id)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Parameters
        ----------
        db: SQLAlchemy session
        email: Email address to search for
        
        Returns
        -------
        Optional[User]
            User if found, None otherwise
        """
        return crud_user.get_by_email(db, email=email)
    
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get multiple users with pagination.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[User]
            List of users
        """
        return crud_user.get_multi(db, skip=skip, limit=limit)
    
    def create_user(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with duplicate email check.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: User creation data
        
        Returns
        -------
        User
            Created user instance
            
        Raises
        ------
        ValidationError
            If a user with the same email already exists
        """
        user = self.get_by_email(db, email=obj_in.email)
        if user:
            raise ValidationError(detail="User with this email already exists")
        return crud_user.create(db, obj_in=obj_in)
    
    def authenticate(self, db: Session, *, email: str, password: str) -> UserWithToken:
        """
        Authenticate a user and return user with access token.
        
        Parameters
        ----------
        db: SQLAlchemy session
        email: User's email
        password: Plaintext password
        
        Returns
        -------
        UserWithToken
            Authenticated user data with JWT token
            
        Raises
        ------
        AuthenticationError
            If authentication fails or user is inactive
        """
        user = crud_user.authenticate(db, email=email, password=password)
        if not user:
            raise AuthenticationError(detail="Incorrect email or password")
        
        if not crud_user.is_active(user):
            raise AuthenticationError(detail="Inactive user")
        
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
    
    def update_user(self, db: Session, *, id: int, obj_in: UserUpdate) -> User:
        """
        Update user with existence check.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: User ID to update
        obj_in: Update data
        
        Returns
        -------
        User
            Updated user instance
            
        Raises
        ------
        NotFoundError
            If user doesn't exist
        """
        user = crud_user.get(db, id)
        if not user:
            raise NotFoundError(detail="User not found")
        return crud_user.update(db, db_obj=user, obj_in=obj_in)
    
    def update_password(self, db: Session, *, user_id: int, new_password: str) -> User:
        """
        Update user password.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        new_password: New plaintext password
        
        Returns
        -------
        User
            Updated user instance
            
        Raises
        ------
        NotFoundError
            If user doesn't exist
        """
        user = crud_user.get(db, user_id)
        if not user:
            raise NotFoundError(detail="User not found")
        
        update_data = {"password": new_password}
        return crud_user.update(db, db_obj=user, obj_in=update_data)
    
    def get_user_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        Dict[str, Any]
            User statistics by role
        """
        from app.domain.models.user import UserRole, User
        
        total = db.query(User).count()
        students = db.query(User).filter(User.role == UserRole.STUDENT).count()
        instructors = db.query(User).filter(User.role == UserRole.INSTRUCTOR).count()
        admins = db.query(User).filter(User.role == UserRole.ADMIN).count()
        
        return {
            "total": total,
            "students": students,
            "instructors": instructors,
            "admins": admins
        }
    
    def get_students(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all student users.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[User]
            List of student users
        """
        return crud_user.get_students(db, skip=skip, limit=limit)
    
    def get_instructors(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get all instructor users.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[User]
            List of instructor users
        """
        return crud_user.get_instructors(db, skip=skip, limit=limit)