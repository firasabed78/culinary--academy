"""
Objective: Implement authentication and user registration endpoints.
This file defines the API endpoints for user authentication, registration,
and retrieving the current user's information.

This file implements the authentication API endpoints:

Purpose: Provides endpoints for user authentication, registration, and profile access.
Key Endpoints:

POST /login: Standard OAuth2 password flow authentication endpoint

Takes username (email) and password
Returns JWT access token for API access


POST /register: User registration endpoint

Takes user creation data (email, password, name, etc.)
Creates a new user account
Returns the created user data (excluding password)


GET /me: Current user profile endpoint

Uses JWT token for authentication
Returns the authenticated user's profile information




Design Patterns:

Separation of Concerns: Routes handle HTTP concerns, service handles business logic
Dependency Injection: Uses FastAPI dependencies for database and authentication
Exception Handling: Custom exceptions mapped to appropriate HTTP responses


Security Features:

OAuth2 password flow authentication
JWT token-based authentication for protected endpoints
Proper HTTP status codes and headers for authentication errors


Integration Points:

Uses authentication dependencies from deps.py
Delegates business logic to UserService
Uses domain schemas for request/response data validation



This file follows RESTful API design principles with clearly defined endpoints for user authentication operations, properly separating concerns between API routing, business logic, and data access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm  # For standard OAuth2 login form
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user  # Authentication dependencies
from app.services.user_service import UserService  # User-related business logic
from app.domain.schemas.user import UserCreate, User, UserWithToken  # Data models/schemas
from app.domain.schemas.token import Token  # Token response schema
from app.core.exceptions import AuthenticationError, ValidationError  # Custom exceptions

# Create a router for authentication endpoints
router = APIRouter()

# Create a service instance for user-related operations
user_service = UserService()

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(get_db),  # Get database session
    form_data: OAuth2PasswordRequestForm = Depends()  # Parse OAuth2 login form
) -> Token:
    """
    Get an access token for future requests using OAuth2 compatible form.
    
    This endpoint authenticates a user with email/password and returns a JWT token.
    Uses the standard OAuth2 password flow where username = email.
    """
    try:
        # Authenticate the user (username in OAuth2 form = email in our system)
        user_with_token = user_service.authenticate(
            db, email=form_data.username, password=form_data.password
        )
        
        # Return the token information
        return Token(
            access_token=user_with_token.access_token,
            token_type=user_with_token.token_type
        )
    except AuthenticationError as e:
        # Handle authentication failures with appropriate HTTP response
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail),
            headers={"WWW-Authenticate": "Bearer"},  # Required by OAuth2 spec
        )

@router.post("/register", response_model=User)
def register(*, db: Session = Depends(get_db), user_in: UserCreate) -> User:
    """
    Create a new user.
    
    This endpoint registers a new user with the provided information.
    Returns the created user object (without password).
    """
    try:
        # Create a new user using the user service
        user = user_service.create_user(db, obj_in=user_in)
        return user
    except ValidationError as e:
        # Handle validation errors with appropriate HTTP response
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail),
        )

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current user information.
    
    This endpoint returns the authenticated user's information.
    Requires a valid JWT token in the Authorization header.
    """
    return current_user