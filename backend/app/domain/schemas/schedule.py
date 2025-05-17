from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import time, date
import time as pytime


class ScheduleBase(BaseModel):
    """Base schema for schedule data."""
    course_id: int
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    location: Optional[str] = None
    is_recurring: bool = True
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v

    @validator('end_time')
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('End time must be after start time')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule."""
    pass


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule."""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    location: Optional[str] = None
    is_recurring: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        if v is not None and not 0 <= v <= 6:
            raise ValueError('Day of week must be between 0 (Monday) and 6 (Sunday)')
        return v


class ScheduleInDB(ScheduleBase):
    """Schema for schedule in database."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Schedule(ScheduleInDB):
    """Schema for schedule API response."""
    pass


class ScheduleWithCourse(Schedule):
    """Schema for schedule with course details."""
    from app.domain.schemas.course import Course

    course: Course