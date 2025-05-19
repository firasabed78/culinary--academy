"""
Test cases for Course CRUD operations.
"""

import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.crud import course as crud_course
from app.domain.schemas.course import CourseCreate, CourseUpdate


@pytest.mark.unit
def test_get_course(db: Session):
    """Test retrieving a course by ID."""
    # Arrange - course created in fixture
    
    # Act
    course = crud_course.get(db, 1)
    
    # Assert
    assert course is not None
    assert course.id == 1
    assert course.title == "Test Culinary Course"


@pytest.mark.unit
def test_get_available_courses(db: Session):
    """Test retrieving available courses."""
    # Arrange - courses created in fixture
    
    # Act
    courses = crud_course.get_available_courses(db)
    
    # Assert
    assert len(courses) >= 2
    assert all(course.is_active for course in courses)
    assert all(course.capacity > 0 for course in courses)


@pytest.mark.unit
def test_get_by_instructor(db: Session):
    """Test retrieving courses by instructor."""
    # Arrange - courses created in fixture with instructor_id = 2
    
    # Act
    courses = crud_course.get_by_instructor(db, instructor_id=2)
    
    # Assert
    assert len(courses) >= 2
    assert all(course.instructor_id == 2 for course in courses)


@pytest.mark.unit
def test_create_course(db: Session):
    """Test creating a new course."""
    # Arrange
    today = date.today()
    course_data = CourseCreate(
        title="New Test Course",
        description="A newly created test course",
        instructor_id=2,
        duration=15,
        price=750.00,
        capacity=10,
        start_date=today + timedelta(days=60),
        end_date=today + timedelta(days=75),
        is_active=True
    )
    
    # Act
    course = crud_course.create(db, obj_in=course_data)
    
    # Assert
    assert course.id is not None
    assert course.title == "New Test Course"
    assert course.price == 750.00
    assert course.capacity == 10
    
    # Verify it can be retrieved
    created_course = crud_course.get(db, course.id)
    assert created_course is not None
    assert created_course.title == "New Test Course"


@pytest.mark.unit
def test_update_course(db: Session):
    """Test updating a course."""
    # Arrange
    course = crud_course.get(db, 1)
    update_data = CourseUpdate(
        title="Updated Course Title",
        price=1200.00
    )
    
    # Act
    updated_course = crud_course.update(db, db_obj=course, obj_in=update_data)
    
    # Assert
    assert updated_course.id == 1
    assert updated_course.title == "Updated Course Title"
    assert updated_course.price == 1200.00
    assert updated_course.description == "A test course for culinary skills"  # Unchanged


@pytest.mark.unit
def test_update_capacity(db: Session):
    """Test updating course capacity."""
    # Arrange
    course = crud_course.get(db, 1)
    original_capacity = course.capacity
    
    # Act - Decrease capacity by 1 (student enrolled)
    updated_course = crud_course.update_capacity(db, course_id=1, change=-1)
    
    # Assert
    assert updated_course.capacity == original_capacity - 1
    
    # Act - Increase capacity by 1 (student unenrolled)
    updated_course = crud_course.update_capacity(db, course_id=1, change=1)
    
    # Assert
    assert updated_course.capacity == original_capacity