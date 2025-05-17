"""
Objective: Define data validation and serialization models for authentication tokens.
This file defines the Pydantic models used for JWT authentication tokens
and their payloads, ensuring consistency in token handling throughout the application.
"""

from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """
    Schema for authentication token.
    
    Represents the token structure returned to clients after successful authentication,
    containing the JWT token itself and its type.
    """
    access_token: str  # The actual JWT token string
    token_type: str  # Token type, typically "bearer"

class TokenPayload(BaseModel):
    """
    Schema for token payload (JWT claims).
    
    Represents the data structure inside the JWT token,
    containing standard JWT claims like subject and expiration.
    """
    sub: Optional[int] = None  # Subject (typically user ID)
    exp: Optional[int] = None  # Expiration timestamp