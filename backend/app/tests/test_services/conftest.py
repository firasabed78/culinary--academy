"""
Test fixtures and configuration for the Culinary Academy Student Registration system.
"""

import pytest
from typing import Dict, Generator, List
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.domain.models.user import User, UserRole
from app.domain.models.course import Course
from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.main import app
from app.api.deps import get_db


# Create test database engine with in-memory SQLite
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)  # Create tables
    yield engine
    Base.metadata.drop_all(bind=engine)  # Drop tables after tests


@pytest.fixture(scope="function")
def db(db_engine):
    """Get test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    # Create test data
    _create_test_data(session)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


def _create_test_data(db: Session):
    """Create test data for testing."""
    # Clear existing data
    db.query(Enrollment).delete()
    db.query(Course).delete()
    db.query(User).delete()
    
    # Create test users
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("adminpass"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    
    instructor = User(
        email="chef@test.com",
        hashed_password=get_password_hash("chefpass"),
        full_name="Test Chef",
        role=UserRole.INSTRUCTOR,
        is_active=True
    )
    db.add(instructor)
    
    student = User(
        email="student@test.com",
        hashed_password=get_password_hash("studentpass"),
        full_name="Test Student",
        role=UserRole.STUDENT,
        is_active=True
    )
    db.add(student)
    
    # Create test courses
    today = date.today()
    course1 = Course(
        title="Test Culinary Course",
        description="A test course for culinary skills",
        instructor_id=2,  # Will be instructor's ID
        duration=30,
        price=1000.00,
        capacity=20,
        start_date=today + timedelta(days=30),
        end_date=today + timedelta(days=60),
        is_active=True
    )
    db.add(course1)
    
    course2 = Course(
        title="Test Baking Course",
        description="A test course for baking",
        instructor_id=2,  # Will be instructor's ID
        duration=20,
        price=800.00,
        capacity=15,
        start_date=today + timedelta(days=45),
        end_date=today + timedelta(days=65),
        is_active=True
    )
    db.add(course2)
    
    # Add enrollment
    enrollment = Enrollment(
        student_id=3,  # Will be student's ID
        course_id=1,   # Will be course1's ID
        status=EnrollmentStatus.APPROVED,
        payment_status=PaymentStatus.PENDING,
        notes="Test enrollment"
    )
    db.add(enrollment)
    
    db.commit()


@pytest.fixture(scope="function")
def client(db):
    """Test client with dependency override."""
    def _get_test_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture(scope="module")
def user_authentication_headers(client: TestClient):
    """Get authentication headers for test user."""
    data = {"email": "student@test.com", "password": "studentpass"}
    response = client.post("/api/v1/auth/login", json=data)
    auth_data = response.json()
    return {"Authorization": f"Bearer {auth_data['access_token']}"}


@pytest.fixture(scope="module")
def admin_authentication_headers(client: TestClient):
    """Get authentication headers for admin user."""
    data = {"email": "admin@test.com", "password": "adminpass"}
    response = client.post("/api/v1/auth/login", json=data)
    auth_data = response.json()
    return {"Authorization": f"Bearer {auth_data['access_token']}"}


@pytest.fixture(scope="module")
def instructor_authentication_headers(client: TestClient):
    """Get authentication headers for instructor user."""
    data = {"email": "chef@test.com", "password": "chefpass"}
    response = client.post("/api/v1/auth/login", json=data)
    auth_data = response.json()
    return {"Authorization": f"Bearer {auth_data['access_token']}"}