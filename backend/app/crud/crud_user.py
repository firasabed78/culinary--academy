"""
crud_user.py - User CRUD operations
This file defines database operations specific to user management in the
Culinary Academy Student Registration system, including authentication
functionality and role-based user operations.
"""

from typing import Any, Dict, Optional, Union, List
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.domain.models.user import User, UserRole
from app.domain.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """CRUD operations for User model with authentication support."""
    
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
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with hashed password.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: User creation data including plaintext password
        
        Returns
        -------
        User
            Created user instance
        """
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            phone=obj_in.phone,
            address=obj_in.address,
            is_active=obj_in.is_active,
            profile_picture=obj_in.profile_picture,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        """
        Update a user, handling password hashing if password is included.
        
        Parameters
        ----------
        db: SQLAlchemy session
        db_obj: Existing user instance to update
        obj_in: Update data, either as UserUpdate model or dict
        
        Returns
        -------
        User
            Updated user instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        if update_data.get("password"):
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        return super().update(db, db_obj=db_obj, obj_in=update_data)
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Parameters
        ----------
        db: SQLAlchemy session
        email: User's email
        password: Plaintext password to verify
        
        Returns
        -------
        Optional[User]
            Authenticated user if credentials are valid, None otherwise
        """
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def is_active(self, user: User) -> bool:
        """
        Check if a user is active.
        
        Parameters
        ----------
        user: User instance
        
        Returns
        -------
        bool
            True if user is active, False otherwise
        """
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        """
        Check if a user has admin role.
        
        Parameters
        ----------
        user: User instance
        
        Returns
        -------
        bool
            True if user is an admin, False otherwise
        """
        return user.role == UserRole.ADMIN
    
    def is_instructor(self, user: User) -> bool:
        """
        Check if a user has instructor role.
        
        Parameters
        ----------
        user: User instance
        
        Returns
        -------
        bool
            True if user is an instructor, False otherwise
        """
        return user.role == UserRole.INSTRUCTOR
    
    def get_students(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Get all users with student role.
        
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
        return (
            db.query(User)
            .filter(User.role == UserRole.STUDENT)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_instructors(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Get all users with instructor role.
        
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
        return (
            db.query(User)
            .filter(User.role == UserRole.INSTRUCTOR)
            .offset(skip)
            .limit(limit)
            .all()
        )