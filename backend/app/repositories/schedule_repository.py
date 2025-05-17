"""
Objective: Implement a specialized repository for schedule operations.
This file extends the base repository with schedule-specific query methods,
providing functionality for managing course schedules and time slot allocations.


The ScheduleRepository specializes in handling course schedules and session times, providing methods to manage and query time-based data in your application.
Key Features:

Schedule Management Operations:

Course Schedules: Retrieving all scheduled sessions for a course
Day-Based Filtering: Finding schedules for specific days of the week
Active Schedule Filtering: Identifying currently active schedules
Time and Date Filtering: Retrieving schedules within specific time ranges


Time-Based Query Patterns:

Time Range Queries: Finding schedules within a specific time of day
Date Range Queries: Finding schedules active during a date range
Overlap Detection: Identifying conflicting schedules for a time slot


Technical Approaches:

Time Overlapping Logic: Implementing algorithms to detect schedule conflicts
NULL Date Handling: Properly handling schedules with open-ended dates
Exclusion Logic: Optionally excluding specific schedules from queries


Notable Implementations:

Conflict Detection: The get_overlapping_schedules method is crucial for preventing double-booking
Date Range Logic: Complex filtering to find schedules active during a period
Course-Schedule Relationship: Methods that link schedules to their courses



This repository plays a vital role in the scheduling and calendar aspects of your culinary academy application, ensuring that:

Course Scheduling: Courses can be assigned appropriate time slots
Conflict Prevention: Time slots don't overlap, preventing double-booking
Calendar Views: Schedules can be filtered by day or time for calendar displays
Schedule Availability: Active and inactive schedules can be distinguished

The repository's methods support various use cases, from creating new schedules while avoiding conflicts, to displaying weekly calendars filtered by day, to finding all courses active during a specific term.
The get_overlapping_schedules method is particularly important as it implements the logic to detect scheduling conflicts, which is essential for maintaining a valid course schedule without double-booked resources or instructors.
With this schedule repository, your application has the necessary data access patterns to support complex scheduling functionality, ensuring that courses can be appropriately scheduled without conflicts while providing users with clear calendar views of available sessions.


"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships
from datetime import date, time
from app.domain.models.schedule import Schedule
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.repositories.base import BaseRepository

class ScheduleRepository(BaseRepository[Schedule, ScheduleCreate, ScheduleUpdate]):
    """
    Repository for schedule operations.
    
    Extends the base repository with schedule-specific queries for
    retrieving, filtering, and managing course schedules.
    """
    
    def __init__(self):
        """Initialize with Schedule model."""
        super().__init__(Schedule)
    
    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """
        Get a schedule with related course data.
        
        Uses eager loading to retrieve a schedule with its associated course
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Schedule ID
            
        Returns:
            Schedule with loaded course relationship or None if not found
        """
        return db.query(self.model)\
            .options(joinedload(self.model.course))\
            .filter(self.model.id == id)\
            .first()
    
    def get_by_course(self, db: Session, *, course_id: int) -> List[Schedule]:
        """
        Get all schedules for a course.
        
        Retrieves all scheduled sessions for a specific course.
        
        Args:
            db: SQLAlchemy database session
            course_id: Course ID
            
        Returns:
            List of schedules for the specified course
        """
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .all()
    
    def get_by_day_of_week(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules for a specific day of the week.
        
        Retrieves all schedules for a particular day of the week (0=Monday, 6=Sunday),
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            day_of_week: Day of week (0-6)
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of schedules for the specified day of week
        """
        return db.query(self.model)\
            .filter(self.model.day_of_week == day_of_week)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_active_schedules(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get all active schedules.
        
        Retrieves all schedules marked as active, with pagination.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of active schedules
        """
        return db.query(self.model)\
            .filter(self.model.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_time_range(
        self, db: Session, *, start_time: time, end_time: time, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules within a time range.
        
        Retrieves schedules that fall within a specific time range during the day,
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            start_time: Earliest start time to include
            end_time: Latest end time to include
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of schedules within the time range
        """
        return db.query(self.model)\
            .filter(
                self.model.start_time >= start_time,
                self.model.end_time <= end_time
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules within a date range.
        
        Retrieves schedules that overlap with a date range, handling schedules
        with no start or end dates appropriately.
        
        Args:
            db: SQLAlchemy database session
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of schedules overlapping with the date range
        """
        return db.query(self.model)\
            .filter(
                # Schedule starts before or on the end_date (or has no start date)
                (self.model.start_date.is_(None) | (self.model.start_date <= end_date)),
                # Schedule ends after or on the start_date (or has no end date)
                (self.model.end_date.is_(None) | (self.model.end_date >= start_date))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_overlapping_schedules(
        self, db: Session, *, day_of_week: int, start_time: time, end_time: time,
        exclude_id: Optional[int] = None
    ) -> List[Schedule]:
        """
        Get schedules that overlap with the given time slot.
        
        Finds schedules that would conflict with a proposed time slot,
        optionally excluding a specific schedule (for updates).
        
        Args:
            db: SQLAlchemy database session
            day_of_week: Day of week (0-6)
            start_time: Start time of the slot to check
            end_time: End time of the slot to check
            exclude_id: Optional schedule ID to exclude from the check
            
        Returns:
            List of schedules that overlap with the proposed time slot
        """
        # A schedule overlaps if:
        # 1. It's on the same day of the week, and
        # 2. Its end time is after the start time we're checking, and
        # 3. Its start time is before the end time we're checking
        query = db.query(self.model).filter(
            self.model.day_of_week == day_of_week,
            self.model.end_time > start_time,
            self.model.start_time < end_time
        )
        
        # Optionally exclude a specific schedule (useful for updates)
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)
            
        return query.all()