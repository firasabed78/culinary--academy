"""
Test cases for User CRUD operations.
"""

import pytest
from sqlalchemy.orm import Session

from app.crud import user as crud_user
from app.domain.schemas.user import UserCreate, UserUpdate
from app.domain.models.user import UserRole


@pytest.mark.unit
def test_create_user(db: Session):
    """Test creating a new user."""
    # Arrange
    user_data = UserCreate(
        email="newuser@test.com",
        password="testpassword",
        full_name="New Test User",
        role=UserRole.STUDENT,
        is_active=True
    )
    
    # Act
    user = crud_user.create(db, obj_in=user_data)
    
    # Assert
    assert user.email == "newuser@test.com"
    assert user.full_name == "New Test User"
    assert user.role == UserRole.STUDENT
    assert user.is_active is True
    assert hasattr(user, "hashed_password")
    assert user.hashed_password != "testpassword"  # Password should be hashed


@pytest.mark.unit
def test_get_user(db: Session):
    """Test retrieving a user by ID."""
    # Arrange - user created in fixture
    
    # Act
    user = crud_user.get(db, 1)
    
    # Assert
    assert user is not None
    assert user.id == 1
    assert user.email == "admin@test.com"


@pytest.mark.unit
def test_get_user_by_email(db: Session):
    """Test retrieving a user by email."""
    # Arrange - user created in fixture
    
    # Act
    user = crud_user.get_by_email(db, email="student@test.com")
    
    # Assert
    assert user is not None
    assert user.email == "student@test.com"
    assert user.role == UserRole.STUDENT


@pytest.mark.unit
def test_update_user(db: Session):
    """Test updating a user."""
    # Arrange
    user = crud_user.get(db, 3)  # Get student user
    update_data = UserUpdate(
        full_name="Updated Student Name",
        phone="123-456-7890"
    )
    
    # Act
    updated_user = crud_user.update(db, db_obj=user, obj_in=update_data)
    
    # Assert
    assert updated_user.id == 3
    assert updated_user.full_name == "Updated Student Name"
    assert updated_user.phone == "123-456-7890"
    assert updated_user.email == "student@test.com"  # Unchanged


@pytest.mark.unit
def test_update_user_password(db: Session):
    """Test updating a user's password."""
    # Arrange
    user = crud_user.get(db, 3)  # Get student user
    old_password_hash = user.hashed_password
    update_data = {"password": "newpassword123"}
    
    # Act
    updated_user = crud_user.update(db, db_obj=user, obj_in=update_data)
    
    # Assert
    assert updated_user.hashed_password != old_password_hash
    # Verify we can authenticate with new password
    authenticated_user = crud_user.authenticate(
        db, email="student@test.com", password="newpassword123"
    )
    assert authenticated_user is not None
    assert authenticated_user.id == 3


@pytest.mark.unit
def test_authenticate_user(db: Session):
    """Test authenticating a user."""
    # Arrange - user created in fixture with password "adminpass"
    
    # Act - Successful authentication
    user = crud_user.authenticate(db, email="admin@test.com", password="adminpass")
    
    # Assert
    assert user is not None
    assert user.email == "admin@test.com"
    
    # Act - Failed authentication
    user_wrong_pass = crud_user.authenticate(
        db, email="admin@test.com", password="wrongpassword"
    )
    user_wrong_email = crud_user.authenticate(
        db, email="nonexisting@test.com", password="adminpass"
    )
    
    # Assert
    assert user_wrong_pass is None
    assert user_wrong_email is None


@pytest.mark.unit
def test_get_users_by_role(db: Session):
    """Test getting users by role."""
    # Arrange - users created in fixture
    
    # Act
    students = crud_user.get_students(db)
    instructors = crud_user.get_instructors(db)
    
    # Assert
    assert len(students) >= 1
    assert students[0].role == UserRole.STUDENT
    
    assert len(instructors) >= 1
    assert instructors[0].role == UserRole.INSTRUCTOR