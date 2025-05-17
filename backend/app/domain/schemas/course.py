"""
Objective: Define data validation and serialization models for course resources.
This file defines the Pydantic models used for validating course-related data
in requests and responses, ensuring type safety and data integrity.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime, date

class CourseBase(BaseModel):
    """
    Base schema for course data.
    
    Contains common fields that are shared across all course schemas,
    serving as the foundation for more specific course models.
    """
    title: str = Field(..., min_length=3, max_length=255)  # Course title
    description: str = Field(..., min_length=10)  # Course description
    instructor_id: Optional[int] = None  # Instructor (may be assigned later)
    price: float = Field(..., ge=0)  # Course price
    capacity: int = Field(..., ge=1)  # Maximum number of students
    category: Optional[str] = None  # Course category
    level: Optional[str] = None  # Course difficulty level
    duration_weeks: Optional[int] = Field(None, ge=1)  # Course duration in weeks
    is_active: bool = True  # Whether course is active and enrollable

    @validator('price')
    def price_must_be_positive_or_zero(cls, v):
        """Validate that price is non-negative."""
        if v < 0:
            raise ValueError('Price must be non-negative')
        return v

class CourseCreate(CourseBase):
    """
    Schema for creating a new course.
    
    Extends the base schema with additional fields required when creating
    a new course, such as start and end dates.
    """
    start_date: Optional[date] = None  # Course start date
    end_date: Optional[date] = None  # Course end date
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate that end date is after start date, if both are provided."""
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class CourseUpdate(BaseModel):
    """
    Schema for updating a course.
    
    Contains fields that can be updated after course creation.
    All fields are optional as updates may only change specific fields.
    """
    title: Optional[str] = Field(None, min_length=3, max_length=255)  # New title
    description: Optional[str] = Field(None, min_length=10)  # New description
    instructor_id: Optional[int] = None  # New instructor
    price: Optional[float] = Field(None, ge=0)  # New price
    capacity: Optional[int] = Field(None, ge=1)  # New capacity
    category: Optional[str] = None  # New category
    level: Optional[str] = None  # New level
    duration_weeks: Optional[int] = Field(None, ge=1)  # New duration
    is_active: Optional[bool] = None  # Update active status
    start_date: Optional[date] = None  # New start date
    end_date: Optional[date] = None  # New end date
    image_url: Optional[str] = None  # New course image URL
    
    @validator('price')
    def price_must_be_positive_or_zero(cls, v):
        """Validate that price is non-negative, if provided."""
        if v is not None and v < 0:
            raise ValueError('Price must be non-negative')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """Validate end date is after start date, if both are provided in the update."""
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class CourseInDB(CourseBase):
    """
    Schema for course in database.
    
    Complete course model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    start_date: Optional[date] = None  # Course start date
    end_date: Optional[date] = None  # Course end date
    image_url: Optional[str] = None  # Course image URL
    enrollment_count: int = 0  # Current number of enrolled students
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Course(CourseInDB):
    """
    Schema for course API response.
    
    The primary model used for API responses containing course data.
    Inherits all fields from CourseInDB.
    """
    pass

class CourseWithDetails(Course):
    """
    Schema for course with details.
    
    Extended course model that includes related entities like
    instructor, schedules, and enrollment information.
    """
    from app.domain.schemas.user import User  # Import needed here to avoid circular imports
    from app.domain.schemas.schedule import Schedule  # Import needed here to avoid circular imports
    
    instructor: Optional[User] = None  # Course instructor
    schedules: List[Schedule] = []  # Course schedules
    active_enrollments: int = 0  # Number of active enrollments
    pending_enrollments: int = 0  # Number of pending enrollments
    completed_enrollments: int = 0  # Number of completed enrollments
    total_revenue: float = 0  # Total revenue from this course