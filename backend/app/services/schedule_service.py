"""
schedule_service.py - Service layer for schedule management
This file handles business logic related to course schedules, including 
creation, validation, and retrieval operations. It enforces scheduling rules
such as preventing overlapping schedules and provides various filtering options
for retrieving schedules by course, instructor, day, or date range.
"""
"""
schedule_service.py - Service layer for schedule management
This file handles business logic related to course schedules, including 
creation, validation, and retrieval operations. It enforces scheduling rules
such as preventing overlapping schedules and provides various filtering options
for retrieving schedules by course, instructor, day, or date range.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date, time

from app.domain.models.schedule import Schedule
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.crud import schedule as crud_schedule
from app.crud import course as crud_course
from app.core.exceptions import NotFoundError, ValidationError


class ScheduleService:
    """Service for schedule operations using CRUD abstractions."""
    
    def get(self, db: Session, id: int) -> Optional[Schedule]:
        """
        Get a schedule by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Schedule ID
        
        Returns
        -------
        Optional[Schedule]
            Schedule if found, None otherwise
        """
        return crud_schedule.get(db, id)
    
    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """
        Get a schedule with course data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Schedule ID
        
        Returns
        -------
        Optional[Schedule]
            Schedule with course data if found
            
        Raises
        ------
        NotFoundError
            If schedule not found
        """
        schedule = crud_schedule.get_with_course(db, id)
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        return schedule
    
    def create_schedule(self, db: Session, *, obj_in: ScheduleCreate) -> Schedule:
        """
        Create a new schedule with validation.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Schedule creation data
        
        Returns
        -------
        Schedule
            Created schedule instance
            
        Raises
        ------
        NotFoundError
            If course not found
        ValidationError
            If schedule overlaps with existing schedule
        """
        # Check if course exists
        course = crud_course.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check for overlapping schedules
        overlapping = crud_schedule.get_overlapping_schedules(
            db, 
            day_of_week=obj_in.day_of_week,
            start_time=obj_in.start_time,
            end_time=obj_in.end_time
        )
        
        if overlapping:
            raise ValidationError(detail="Schedule overlaps with existing schedule")
        
        # Create schedule
        return crud_schedule.create(db, obj_in=obj_in)
    
    def update_schedule(
        self, db: Session, *, id: int, obj_in: ScheduleUpdate
    ) -> Schedule:
        """
        Update a schedule with validation.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Schedule ID
        obj_in: Update data
        
        Returns
        -------
        Schedule
            Updated schedule instance
            
        Raises
        ------
        NotFoundError
            If schedule not found
        ValidationError
            If schedule would overlap with existing schedule
        """
        schedule = crud_schedule.get(db, id)
        if not schedule:
            raise NotFoundError(detail="Schedule not found")
        
        # If updating time or day, check for overlaps
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
            overlapping = crud_schedule.get_overlapping_schedules(
                db, 
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                exclude_id=id
            )
            
            if overlapping:
                raise ValidationError(detail="Schedule would overlap with existing schedule")
        
        # Update schedule after validation passes
        return crud_schedule.update(db, db_obj=schedule, obj_in=obj_in)
    
    def get_course_schedules(
        self, db: Session, *, course_id: int
    ) -> List[Schedule]:
        """
        Get all schedules for a course.
        
        Parameters
        ----------
        db: SQLAlchemy session
        course_id: Course ID
        
        Returns
        -------
        List[Schedule]
            List of course schedules
        """
        return crud_schedule.get_by_course(db, course_id=course_id)
    
    def get_schedules_by_day(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules for a specific day.
        
        Parameters
        ----------
        db: SQLAlchemy session
        day_of_week: Day of week (0=Sunday, 6=Saturday)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Schedule]
            List of schedules on the specified day
        """
        return crud_schedule.get_by_day_of_week(db, day_of_week=day_of_week, skip=skip, limit=limit)
    
    def get_schedules_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules within a date range.
        
        Parameters
        ----------
        db: SQLAlchemy session
        start_date: Start date of range
        end_date: End date of range
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Schedule]
            List of schedules within the date range
        """
        return crud_schedule.get_by_date_range(db, start_date=start_date, end_date=end_date, skip=skip, limit=limit)
    
    def get_instructor_schedules(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules for courses taught by an instructor.
        
        Parameters
        ----------
        db: SQLAlchemy session
        instructor_id: Instructor ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Schedule]
            List of instructor schedules
        """
        # Get courses for instructor
        courses = crud_course.get_by_instructor(db, instructor_id=instructor_id)
        if not courses:
            return []
        
        course_ids = [course.id for course in courses]
        
        # Get schedules for these courses
        schedules = []
        for course_id in course_ids:
            course_schedules = crud_schedule.get_by_course(db, course_id=course_id)
            schedules.extend(course_schedules)
        
        # Manual pagination (note: this approach is inefficient for large datasets)
        return schedules[skip:skip+limit]
    
    def get_kitchen_availability(
        self, db: Session, *, location: str, start_date: date, end_date: date
    ) -> Dict[str, Any]:
        """
        Get kitchen availability for a specific location and date range.
        
        Parameters
        ----------
        db: SQLAlchemy session
        location: Kitchen location
        start_date: Start date of availability check
        end_date: End date of availability check
        
        Returns
        -------
        Dict[str, Any]
            Kitchen availability by day and time slot
        """
        return crud_schedule.get_kitchen_availability(
            db, location=location, start_date=start_date, end_date=end_date
        )