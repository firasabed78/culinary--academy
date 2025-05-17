# backend/app/repositories/user_repository.py
from typing import Optional
from sqlalchemy.orm import Session

from app.domain.models.user import User
from app.domain.schemas.user import UserCreate, UserUpdate
from app.repositories.base import BaseRepository
from app.core.security import get_password_hash, verify_password


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for user operations."""
    
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """Get a user by email."""
        return db.query(User).filter(User.email == email).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """Create a new user with password hashing."""
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            role=obj_in.role,
            phone=obj_in.phone,
            address=obj_in.address,
            is_active=obj_in.is_active,
            profile_picture=obj_in.profile_picture
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password."""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """Check if user is active."""
        return user.is_active

    def is_admin(self, user: User) -> bool:
        """Check if user is admin."""
        return user.role == "admin"

    def is_instructor(self, user: User) -> bool:
        """Check if user is instructor."""
        return user.role == "instructor"

    def update_password(self, db: Session, *, user: User, new_password: str) -> User:
        """Update user password."""
        hashed_password = get_password_hash(new_password)
        user.hashed_password = hashed_password
        db.add(user)
        db.commit()
        db.refresh(user)
        return user