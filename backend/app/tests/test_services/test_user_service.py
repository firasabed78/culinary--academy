"""
Test cases for User Service operations.
"""

import pytest
from datetime import timedelta
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.domain.schemas.user import UserCreate, UserUpdate
from app.domain.models.user import UserRole
from app.core.exceptions import ValidationError, NotFoundError, AuthenticationError


@pytest.fixture
def user_service():
    """User service fixture."""
    return UserService()


@pytest.mark.unit
def test_create_user(db: Session, user_service):
    """Test creating a user with the service layer."""
    # Arrange
    user_data = UserCreate(
        email="serviceuser@test.com",
        password="servicepass",
        full_name="Service Test User",
        role=UserRole.STUDENT,
        is_active=True
    )
    
    # Act
    user = user_service.create_user(db, obj_in=user_data)
    
    # Assert
    assert user.email == "serviceuser@test.com"
    assert user.full_name == "Service Test User"
    
    # Verify duplicate email check
    with pytest.raises(ValidationError):
        user_service.create_user(db, obj_in=user_data)


@pytest.mark.unit
def test_authenticate(db: Session, user_service):
    """Test authenticating a user with the service layer."""
    # Arrange - user created in fixture
    
    # Act - Successful authentication
    user_with_token = user_service.authenticate(
        db, email="admin@test.com", password="adminpass"
    )
    
    # Assert
    assert user_with_token.email == "admin@test.com"
    assert user_with_token.access_token is not None
    assert user_with_token.token_type == "bearer"
    
    # Act/Assert - Failed authentication
    with pytest.raises(AuthenticationError):
        user_service.authenticate(
            db, email="admin@test.com", password="wrongpassword"
        )
    
    with pytest.raises(AuthenticationError):
        user_service.authenticate(
            db, email="nonexistent@test.com", password="adminpass"
        )


@pytest.mark.unit
def test_update_user(db: Session, user_service):
    """Test updating a user with the service layer."""
    # Arrange
    update_data = UserUpdate(
        full_name="Service Updated Name",
        phone="987-654-3210"
    )
    
    # Act
    updated_user = user_service.update_user(db, id=3, obj_in=update_data)
    
    # Assert
    assert updated_user.full_name == "Service Updated Name"
    assert updated_user.phone == "987-654-3210"
    
    # Act/Assert - Test not found error
    with pytest.raises(NotFoundError):
        user_service.update_user(db, id=999, obj_in=update_data)


@pytest.mark.unit
def test_update_password(db: Session, user_service):
    """Test updating a user's password with the service layer."""
    # Arrange
    user_id = 3
    new_password = "newservicepass"
    
    # Act
    updated_user = user_service.update_password(
        db, user_id=user_id, new_password=new_password
    )
    
    # Assert - Check if we can authenticate with the new password
    user_with_token = user_service.authenticate(
        db, email="student@test.com", password=new_password
    )
    assert user_with_token is not None
    assert user_with_token.id == user_id
    
    # Act/Assert - Test not found error
    with pytest.raises(NotFoundError):
        user_service.update_password(
            db, user_id=999, new_password=new_password
        )