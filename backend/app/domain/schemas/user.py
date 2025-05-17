"""
Objective: Define data validation and serialization models for user resources.
This file defines the Pydantic models used for validating user-related data
in requests and responses, ensuring type safety and data integrity.
"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
import re

class UserBase(BaseModel):
    """
    Base schema for user data.
    
    Contains common fields that are shared across all user schemas,
    serving as the foundation for more specific user models.
    """
    email: EmailStr  # Email address (with validation)
    first_name: str = Field(..., min_length=1, max_length=100)  # First name
    last_name: str = Field(..., min_length=1, max_length=100)  # Last name
    is_active: bool = True  # Whether the user account is active
    role: str = "student"  # User role (default to student)
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that role is one of the allowed values."""
        allowed_roles = ["admin", "instructor", "student", "staff"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v

class UserCreate(UserBase):
    """
    Schema for creating a new user.
    
    Extends the base schema with additional fields required when creating
    a new user, particularly the password field with validation.
    """
    password: str = Field(..., min_length=8)  # Password (min 8 chars)
    
    @validator('password')
    def password_strength(cls, v):
        """
        Validate password strength.
        
        Ensures that passwords meet security requirements like containing
        uppercase, lowercase, numbers, and special characters.
        """
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseModel):
    """
    Schema for updating a user.
    
    Contains fields that can be updated after user creation.
    All fields are optional as updates may only change specific fields.
    """
    email: Optional[EmailStr] = None  # New email
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)  # New first name
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)  # New last name
    password: Optional[str] = Field(None, min_length=8)  # New password
    is_active: Optional[bool] = None  # Update active status
    role: Optional[str] = None  # New role
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that role is one of the allowed values, if provided."""
        if v is not None:
            allowed_roles = ["admin", "instructor", "student", "staff"]
            if v not in allowed_roles:
                raise ValueError(f"Role must be one of: {', '.join(allowed_roles)}")
        return v
    
    @validator('password')
    def password_strength(cls, v):
        """Validate password strength if password is being updated."""
        if v is not None:
            if not re.search(r'[A-Z]', v):
                raise ValueError('Password must contain at least one uppercase letter')
            if not re.search(r'[a-z]', v):
                raise ValueError('Password must contain at least one lowercase letter')
            if not re.search(r'[0-9]', v):
                raise ValueError('Password must contain at least one number')
            if not re.search(r'[^A-Za-z0-9]', v):
                raise ValueError('Password must contain at least one special character')
        return v

class UserInDB(UserBase):
    """
    Schema for user in database.
    
    Complete user model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    hashed_password: str  # Hashed password (not accessible in API responses)
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class User(BaseModel):
    """
    Schema for user API response.
    
    The primary model used for API responses containing user data.
    Similar to UserInDB but without the password hash.
    """
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class UserWithToken(User):
    """
    Schema for user with authentication token.
    
    Extended user model that includes an authentication token,
    typically used for login responses.
    """
    access_token: str  # JWT access token
    token_type: str  # Token type (e.g., "bearer")

class UserWithEnrollments(User):
    """
    Schema for user with enrollments.
    
    Extended user model that includes the user's enrollments,
    typically used for student profile views.
    """
    from app.domain.schemas.enrollment import Enrollment  # Import needed here to avoid circular imports
    enrollments: List[Enrollment] = []  # User's enrollments