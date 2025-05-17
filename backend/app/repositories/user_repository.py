"""
Objective: Implement a specialized repository for user operations.
This file extends the base repository with user-specific query methods,
providing functionality for user authentication, authorization, and management.

The UserRepository is a crucial component of your application's security and user management system, providing specialized methods for user authentication, authorization checks, and secure password handling.
Key Features:

User Authentication:

Email-Based Lookup: Finding users by their unique email addresses
Password Verification: Securely verifying password hashes
Authentication Flow: Combined email and password verification


Secure Password Management:

Password Hashing: Proper security for storing user passwords
Password Updates: Secure method for changing passwords
Hash Verification: Checking passwords without storing in plain text


Authorization Checks:

Role Verification: Methods to check user roles (admin, instructor)
Account Status: Checking if a user account is active
Permission Helpers: Convenience methods for permission checks


Security-Enhanced Operations:

Custom Creation Logic: Overridden create method to handle password hashing
Secure Authentication: Proper credential verification workflow
Separation of Concerns: Clear distinction between authentication and authorization



This repository implements several important security best practices:

Never storing plain-text passwords: Both during creation and updates, passwords are always hashed
Constant-time password comparison: Using secure verification functions to prevent timing attacks
Role-based access control: Helper methods for checking user permissions
Proper authentication flow: Clear, secure process for verifying user credentials

The repository serves as the foundation for your application's authentication system, working alongside the security utilities to provide robust user management. It enables:

User registration: Creating new user accounts with secure password storage
User login: Authenticating users with their credentials
Permission checks: Determining user access levels for authorization
Password management: Securely updating user passwords

The methods in this repository are particularly important for the authentication endpoints and middleware in your API, ensuring that user identities are properly verified and access is appropriately controlled based on user roles and account status

"""

from typing import Optional
from sqlalchemy.orm import Session
from app.domain.models.user import User
from app.domain.schemas.user import UserCreate, UserUpdate
from app.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password  # Password utility functions

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """
    Repository for user operations.
    
    Extends the base repository with user-specific queries and methods
    for user management, authentication, and authorization checks.
    """
    
    def __init__(self):
        """Initialize with User model."""
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Retrieves a user by their unique email address, useful for
        authentication and user lookup.
        
        Args:
            db: SQLAlchemy database session
            email: User's email address
            
        Returns:
            Matching user or None if not found
        """
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Create a new user with password hashing.
        
        Overrides the base create method to properly hash the user's
        password before storing it in the database.
        
        Args:
            db: SQLAlchemy database session
            obj_in: User creation data with plain-text password
            
        Returns:
            Created user object
        """
        # Create user with hashed password
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),  # Hash password
            full_name=obj_in.full_name,
            role=obj_in.role,
            phone=obj_in.phone,
            address=obj_in.address,
            is_active=obj_in.is_active,
            profile_picture=obj_in.profile_picture
        )
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get generated values
        return db_obj
    
    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.
        
        Verifies user credentials by checking the provided email and password
        against stored values, with proper password hashing.
        
        Args:
            db: SQLAlchemy database session
            email: User's email address
            password: Plain-text password to verify
            
        Returns:
            Authenticated user or None if authentication fails
        """
        # Get user by email
        user = self.get_by_email(db, email=email)
        if not user:
            return None  # User not found
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            return None  # Incorrect password
        
        return user  # Authentication successful
    
    def is_active(self, user: User) -> bool:
        """
        Check if user is active.
        
        Determines if a user account is currently active,
        used for access control.
        
        Args:
            user: User object to check
            
        Returns:
            True if user is active, False otherwise
        """
        return user.is_active
    
    def is_admin(self, user: User) -> bool:
        """
        Check if user is admin.
        
        Determines if a user has administrator privileges,
        used for permission checks.
        
        Args:
            user: User object to check
            
        Returns:
            True if user is an admin, False otherwise
        """
        return user.role == "admin"
    
    def is_instructor(self, user: User) -> bool:
        """
        Check if user is instructor.
        
        Determines if a user has instructor privileges,
        used for permission checks.
        
        Args:
            user: User object to check
            
        Returns:
            True if user is an instructor, False otherwise
        """
        return user.role == "instructor"
    
    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """
        Update user password.
        
        Changes a user's password, properly hashing the new password
        before storing it.
        
        Args:
            db: SQLAlchemy database session
            user: User object to update
            new_password: New plain-text password
            
        Returns:
            Updated user object
        """
        # Hash the new password
        hashed_password = get_password_hash(new_password)
        
        # Update user's password
        user.hashed_password = hashed_password
        db.add(user)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(user)  # Refresh to get updated values
        return user