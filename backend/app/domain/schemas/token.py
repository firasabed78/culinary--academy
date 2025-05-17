from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Schema for token payload (JWT claims)."""
    sub: Optional[int] = None
    exp: Optional[int] = None