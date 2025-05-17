"""
Objective: Define data validation and serialization models for schedule resources.
This file defines the Pydantic models used for validating schedule-related data
in requests and responses, ensuring type safety and data integrity with specific
validation for time-related constraints.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import time, date, datetime  # Missing import in original
import time as pytime  # Python's time module for additional time operations

class ScheduleBase(BaseModel):
    """
    Base schema for schedule data.
    
    Contains common fields shared across all schedule schemas,
    with specific validation rules for date and time fields.
    """
    course_id: int  # The course this schedule belongs to
    day_of_week: int = Field(..., ge=0, le=6)  # Day of week (0=Monday, 6=Sunday)
    start_time: time  # Session start time
    end_time: time  # Session end time
    location: Optional[str] = None  # Optional classroom/location information
    is_recurring: bool = True  # Whether this schedule repeats weekly
    start_date: Optional[date] = None  # First session date (for non-recurring)
    end_date: Optional[date] = None  # Last session date (for non-recurring or term end)
    is_active: bool = True  # Whether this schedule is active
    
    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        """
        Validate day of week is between 0-6.
        
        Ensures the day of week value is valid (0=Monday through 6=Sunday).
        """
        if not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v
    
    @validator('end_time')
    def validate_end_time(cls, v, values):
        """
        Validate end time is after start time.
        
        Ensures that the session end time is later than the start time,
        preventing invalid time ranges.
        """
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        """
        Validate end date is after start date.
        
        For date ranges, ensures that the end date is later than the start date,
        preventing invalid date ranges.
        """
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class ScheduleCreate(ScheduleBase):
    """
    Schema for creating a new schedule.
    
    Extends the base schema without adding additional fields,
    inheriting all validation rules from the base model.
    """
    pass

class ScheduleUpdate(BaseModel):
    """
    Schema for updating a schedule.
    
    Contains fields that can be updated after schedule creation.
    All fields are optional as updates may only change specific fields,
    but still include appropriate validation rules.
    """
    day_of_week: Optional[int] = Field(None, ge=0, le=6)  # New day of week
    start_time: Optional[time] = None  # New start time
    end_time: Optional[time] = None  # New end time
    location: Optional[str] = None  # New location
    is_recurring: Optional[bool] = None  # Update recurring status
    start_date: Optional[date] = None  # New start date
    end_date: Optional[date] = None  # New end date
    is_active: Optional[bool] = None  # Update active status
    
    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        """
        Validate day of week is between 0-6 when provided.
        
        Same validation as in base model, but handles None values
        since this field is optional for updates.
        """
        if v is not None and not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v

class ScheduleInDB(ScheduleBase):
    """
    Schema for schedule in database.
    
    Complete schedule model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Schedule(ScheduleInDB):
    """
    Schema for schedule API response.
    
    The primary model used for API responses containing schedule data.
    Inherits all fields from ScheduleInDB.
    """
    pass

class ScheduleWithCourse(Schedule):
    """
    Schema for schedule with course details.
    
    Extended schedule model that includes the associated course's information,
    typically used for detailed schedule views.
    """
    from app.domain.schemas.course import Course  # Import needed here to avoid circular imports
    course: Course  # The course this schedule belongs to