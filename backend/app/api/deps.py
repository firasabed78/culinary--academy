# backend/app/api/deps.py
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import ALGORITHM
from app.db.session import SessionLocal
from app.domain.models.user import User
from app.repositories.user_repository import UserRepository
from app.domain.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
user_repository = UserRepository()

def get_db() -> Generator:
    """Dependency for database session."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Dependency for getting the current user."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = user_repository.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency for getting the current active user."""
    if not user_repository.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    return current_user

def get_current_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency for getting the current admin user."""
    if not user_repository.is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    
    return current_user

def get_current_instructor_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Dependency for getting the current instructor or admin user."""
    if not (user_repository.is_admin(current_user) or user_repository.is_instructor(current_user)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="The user doesn't have enough privileges"
        )
    
    return current_user