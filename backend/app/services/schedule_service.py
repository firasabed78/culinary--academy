from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, time

from app.domain.models.schedule import Schedule
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.repositories.schedule_repository import ScheduleRepository
from app.repositories.course_repository import CourseRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError


class ScheduleService(BaseService[Schedule, ScheduleCreate, ScheduleUpdate, ScheduleRepository]):
    """Service for schedule operations."""
    
    def __init__(self):
        super().__init__(ScheduleRepository)
        self.course_repository = CourseRepository()
    
    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """Get a schedule with course data."""
        schedule = self.repository.get_with_course(db, id)
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        return schedule
    
    def create_schedule(self, db: Session, *, obj_in: ScheduleCreate) -> Schedule:
        """Create a new schedule with validation."""
        # Check if course exists
        course = self.course_repository.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check for overlapping schedules
        overlapping = self.repository.get_overlapping_schedules(
            db, 
            day_of_week=obj_in.day_of_week,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time
        )
        
        if overlapping:
            raise ValidationError(detail="Schedule overlaps with existing schedule")
        
        # Create schedule
        return self.repository.create(db, obj_in=obj_in)
    
    def update_schedule(
        self, db: Session, *, id: int, obj_in: ScheduleUpdate
    ) -> Schedule:
        """Update a schedule with validation."""
        schedule = self.repository.get(db, id)
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        
        # If updating time or day, check for overlaps
        if (
            obj_in.day_of_week is not None or 
            obj_in.start_time is not None or 
            obj_in.end_time is not None
        ):
            day_of_week = obj_in.day_of_week if obj_in.day_of_week is not None else schedule.day_of_week
            start_time = obj_in.start_time if obj_in.start_time is not None else schedule.start_time
            end_time = obj_in.end_time if obj_in.end_time is not None else schedule.end_time
            
            overlapping = self.repository.get_overlapping_schedules(
                db, 
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                exclude_id=id
            )
            
            if overlapping:
                raise ValidationError(detail="Schedule would overlap with existing schedule")
        
        # Update schedule
        return self.update(db, id=id, obj_in=obj_in)
    
    def get_course_schedules(
        self, db: Session, *, course_id: int
    ) -> List[Schedule]:
        """Get all schedules for a course."""
        return self.repository.get_by_course(db, course_id=course_id)
    
    def get_schedules_by_day(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules for a specific day."""
        return self.repository.get_by_day_of_week(db, day_of_week=day_of_week, skip=skip, limit=limit)
    
    def get_schedules_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules within a date range."""
        return self.repository.get_by_date_range(db, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    
    def get_instructor_schedules(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules for courses taught by an instructor."""
        # Get courses for instructor
        courses = self.course_repository.get_by_instructor(db, instructor_id=instructor_id)
        if not courses:
            return []
        
        course_ids = [course.id for course in courses]
        
        # Get schedules for these courses
        schedules = []
        for course_id in course_ids:
            course_schedules = self.repository.get_by_course(db, course_id=course_id)
            schedules.extend(course_schedules)
        
        # Manual pagination (this is not efficient for large datasets)
        return schedules[skip:skip+limit]