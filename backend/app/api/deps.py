"""
Objective: Define reusable dependencies for the API endpoints.
This file contains common dependencies used across API endpoints, including
database session management, user authentication, and permission validation.
This file implements the dependency injection pattern for FastAPI routes:

Purpose: Provides reusable dependencies for API endpoints, centralizing authentication and authorization logic.
Key Features:

Database session management with proper cleanup
JWT token validation and user authentication
Role-based access control (RBAC) with different permission levels:

Active users (basic authenticated users)
Admin users (full administrative access)
Instructors (special permissions for teaching staff)




Design Patterns:

Dependency Injection: Uses FastAPI's dependency system
Single Responsibility: Each function handles one specific aspect of authentication/authorization
Chain of Dependencies: Builds more specific permissions on top of more general ones


Security Aspects:

OAuth2 password flow implementation
JWT token validation
Proper HTTP status codes and headers for authentication errors
Role-based access control (RBAC)


Integration Points:

Uses the database session from the DB module
Uses security settings and algorithms from core module
Works with the user repository for database operations
Applied to API endpoints that require authentication/authorization



This file is crucial for enforcing security across the API and follows the principle of "authenticate once, authorize as needed" by separating the authentication process from the various authorization checks.

"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer  # FastAPI's OAuth2 password flow
from sqlalchemy.orm import Session
from jose import jwt, JWTError  # JWT token handling
from pydantic import ValidationError
from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.domain.models.user import User
from app.repositories.user_repository import UserRepository
from app.domain.schemas.token import TokenPayload

# Configure OAuth2 with the token endpoint URL
# This sets up the authentication scheme for the API
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

# Create an instance of the user repository for user-related operations
user_repository = UserRepository()

def get_db() -> Generator:
    """
    Dependency for database session.
    
    Creates a new database session for each request and ensures it's closed
    after the request is processed, even if an exception occurs.
    """
    try:
        db = SessionLocal()  # Create a new database session
        yield db  # Provide the session to the endpoint
    finally:
        db.close()  # Ensure the session is closed after use

def get_current_user(
    db: Session = Depends(get_db),  # Get database session
    token: str = Depends(oauth2_scheme)  # Get JWT token from request
) -> User:
    """
    Dependency for getting the current authenticated user.
    
    Validates the JWT token, decodes it, and returns the corresponding user.
    Raises appropriate HTTP exceptions if authentication fails.
    """
    try:
        # Decode and validate the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)  # Parse token data using Pydantic model
    except (JWTError, ValidationError):
        # If token is invalid, raise 401 Unauthorized
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},  # Required by OAuth2 spec
        )
    
    # Get the user from the database using the user ID from the token
    user = user_repository.get(db, id=token_data.sub)
    if not user:
        # If user not found, raise 404 Not Found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency for getting the current active user.
    
    Ensures the authenticated user is active (not disabled).
    """
    if not user_repository.is_active(current_user):
        # If user is inactive, raise 400 Bad Request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency for getting the current admin user.
    
    Ensures the authenticated user has admin privileges.
    """
    if not user_repository.is_admin(current_user):
        # If user is not an admin, raise 403 Forbidden
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_instructor_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency for getting the current instructor or admin user.
    
    Ensures the authenticated user has instructor or admin privileges.
    """
    if not (user_repository.is_admin(current_user) or user_repository.is_instructor(current_user)):
        # If user is neither an admin nor an instructor, raise 403 Forbidden
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user