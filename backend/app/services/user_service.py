# backend/app/services/user_service.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import timedelta

from app.domain.models.user import User
from app.domain.schemas.user import UserCreate, UserUpdate, UserWithToken
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService
from app.core.security import create_access_token
from app.core.config import settings
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError


class UserService(BaseService[User, UserCreate, UserUpdate, UserRepository]):
    """Service for user operations."""
    
    def __init__(self):
        super().__init__(UserRepository)

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email."""
        return self.repository.get_by_email(db, email=email)

    def create_user(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with duplicate email check."""
        user = self.get_by_email(db, email=obj_in.email)
        if user:
            raise ValidationError(detail="User with this email already exists")
        return self.repository.create(db, obj_in=obj_in)

    def authenticate(self, db: Session, *, email: str, password: str) -> UserWithToken:
        """Authenticate a user and return user with access token."""
        user = self.repository.authenticate(db, email=email, password=password)
        if not user:
            raise AuthenticationError(detail="Incorrect email or password")
        if not self.repository.is_active(user):
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
        """Update user with existence check."""
        user = self.get(db, id)
        if not user:
            raise NotFoundError(detail="User not found")
        return self.update(db, id=id, obj_in=obj_in)

    def update_password(self, db: Session, *, user_id: int, new_password: str) -> User:
        """Update user password."""
        user = self.get(db, user_id)
        if not user:
            raise NotFoundError(detail="User not found")
        return self.repository.update_password(db, user=user, new_password=new_password)

    def get_user_stats(self, db: Session) -> Dict[str, Any]:
        """Get user statistics."""
        total = db.query(User).count()
        students = db.query(User).filter(User.role == "student").count()
        instructors = db.query(User).filter(User.role == "instructor").count()
        admins = db.query(User).filter(User.role == "admin").count()
        
        return {
            "total": total,
            "students": students,
            "instructors": instructors,
            "admins": admins
        }