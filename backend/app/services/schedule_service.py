"""
schedule_service.py - Service layer for schedule management
This file handles business logic related to course schedules, including 
creation, validation, and retrieval operations. It enforces scheduling rules
such as preventing overlapping schedules and provides various filtering options
for retrieving schedules by course, instructor, day, or date range.
"""

from typing import List, Optional, Dict, Any  # Import type hints for function signatures
from sqlalchemy.orm import Session  # Import SQLAlchemy session for database operations
from datetime import date, time  # Import date and time types for schedule handling

from app.domain.models.schedule import Schedule  # Import the Schedule model
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate  # Import Schedule schemas for data validation
from app.repositories.schedule_repository import ScheduleRepository  # Import repository for schedule DB operations
from app.repositories.course_repository import CourseRepository  # Import course repository to check course existence
from app.services.base import BaseService  # Import base service with common CRUD operations
from app.core.exceptions import NotFoundError, ValidationError  # Import custom exceptions


class ScheduleService(BaseService[Schedule, ScheduleCreate, ScheduleUpdate, ScheduleRepository]):
    """Service for schedule operations."""
    
    def __init__(self):
        # Initialize with schedule repository
        super().__init__(ScheduleRepository)
        # Create course repository instance to validate course existence
        self.course_repository = CourseRepository()
    
    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """Get a schedule with course data."""
        # Retrieve schedule with joined course data
        schedule = self.repository.get_with_course(db, id)
        # Raise exception if schedule not found
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        # Return the schedule with course data
        return schedule
    
    def create_schedule(self, db: Session, *, obj_in: ScheduleCreate) -> Schedule:
        """Create a new schedule with validation."""
        # Verify course exists before creating schedule
        course = self.course_repository.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check for overlapping schedules to prevent conflicts
        overlapping = self.repository.get_overlapping_schedules(
            db, 
            day_of_week=obj_in.day_of_week,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time
        )
        
        # Prevent creation if schedule would overlap with existing ones
        if overlapping:
            raise ValidationError(detail="Schedule overlaps with existing schedule")
        
        # Create schedule in database after validation passes
        return self.repository.create(db, obj_in=obj_in)
    
    def update_schedule(
        self, db: Session, *, id: int, obj_in: ScheduleUpdate
    ) -> Schedule:
        """Update a schedule with validation."""
        # Find schedule by ID
        schedule = self.repository.get(db, id)
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        
        # If updating time or day, check for overlaps with other schedules
        if (
            obj_in.day_of_week is not None or 
            obj_in.start_time is not None or 
            obj_in.end_time is not None
        ):
            # Use new values if provided, otherwise keep existing values
            day_of_week = obj_in.day_of_week if obj_in.day_of_week is not None else schedule.day_of_week
            start_time = obj_in.start_time if obj_in.start_time is not None else schedule.start_time
            end_time = obj_in.end_time if obj_in.end_time is not None else schedule.end_time
            
            # Check for overlapping schedules, excluding the current one
            overlapping = self.repository.get_overlapping_schedules(
                db, 
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                exclude_id=id  # Exclude current schedule from overlap check
            )
            
            # Prevent update if it would create a schedule conflict
            if overlapping:
                raise ValidationError(detail="Schedule would overlap with existing schedule")
        
        # Update schedule after validation passes
        return self.update(db, id=id, obj_in=obj_in)
    
    def get_course_schedules(
        self, db: Session, *, course_id: int
    ) -> List[Schedule]:
        """Get all schedules for a course."""
        # Retrieve all schedules associated with the specified course
        return self.repository.get_by_course(db, course_id=course_id)
    
    def get_schedules_by_day(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules for a specific day."""
        # Retrieve schedules for a specific day of the week with pagination
        return self.repository.get_by_day_of_week(db, day_of_week=day_of_week, skip=skip, limit=limit)
    
    def get_schedules_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules within a date range."""
        # Retrieve schedules that fall within the specified date range with pagination
        return self.repository.get_by_date_range(db, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    
    def get_instructor_schedules(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules for courses taught by an instructor."""
        # First get all courses taught by the instructor
        courses = self.course_repository.get_by_instructor(db, instructor_id=instructor_id)
        if not courses:
            return []  # Return empty list if instructor has no courses
        
        # Extract course IDs from the courses list
        course_ids = [course.id for course in courses]
        
        # Get schedules for each course and combine them
        schedules = []
        for course_id in course_ids:
            course_schedules = self.repository.get_by_course(db, course_id=course_id)
            schedules.extend(course_schedules)
        
        # Manual pagination (note: this approach is inefficient for large datasets)
        return schedules[skip:skip+limit]