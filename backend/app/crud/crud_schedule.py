"""
crud_schedule.py - Schedule CRUD operations
This file defines database operations for managing culinary course schedules,
including time slot management, kitchen availability checks, and specialized
filtering methods.
"""

from typing import List, Optional
from datetime import date, time
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.crud.base import CRUDBase
from app.domain.models.schedule import Schedule
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate


class CRUDSchedule(CRUDBase[Schedule, ScheduleCreate, ScheduleUpdate]):
    """CRUD operations for Schedule model with kitchen scheduling capabilities."""
    
    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """
        Get schedule with course data joined.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Schedule ID
        
        Returns
        -------
        Optional[Schedule]
            Schedule with course data if found, None otherwise
        """
        return (
            db.query(Schedule)
            .filter(Schedule.id == id)
            .first()
        )
    
    def get_by_course(
        self, db: Session, *, course_id: int
    ) -> List[Schedule]:
        """
        Get all schedules for a specific course.
        
        Parameters
        ----------
        db: SQLAlchemy session
        course_id: ID of the course
        
        Returns
        -------
        List[Schedule]
            List of course schedules
        """
        return (
            db.query(Schedule)
            .filter(Schedule.course_id == course_id)
            .all()
        )
    
    def get_by_day_of_week(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """
        Get schedules for a specific day of the week.
        
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
        return (
            db.query(Schedule)
            .filter(Schedule.day_of_week == day_of_week)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_date_range(
        self,
        db: Session,
        *,
        start_date: date,
        end_date: date,
        skip: int = 0,
        limit: int = 100
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
        return (
            db.query(Schedule)
            .filter(
                and_(
                    or_(Schedule.start_date == None, Schedule.start_date <= end_date),
                    or_(Schedule.end_date == None, Schedule.end_date >= start_date),
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_overlapping_schedules(
        self,
        db: Session,
        *,
        day_of_week: int,
        start_time: time,
        end_time: time,
        exclude_id: Optional[int] = None
    ) -> List[Schedule]:
        """
        Find schedules that overlap with the given time slot.
        
        Parameters
        ----------
        db: SQLAlchemy session
        day_of_week: Day of week (0=Sunday, 6=Saturday)
        start_time: Start time of the slot
        end_time: End time of the slot
        exclude_id: Schedule ID to exclude from check (for updates)
        
        Returns
        -------
        List[Schedule]
            List of overlapping schedules
        """
        query = (
            db.query(Schedule)
            .filter(
                and_(
                    Schedule.day_of_week == day_of_week,
                    Schedule.start_time < end_time,
                    Schedule.end_time > start_time,
                    Schedule.is_active == True,
                )
            )
        )
        
        if exclude_id is not None:
            query = query.filter(Schedule.id != exclude_id)
        
        return query.all()
    
    def get_kitchen_availability(
        self, db: Session, *, location: str, start_date: date, end_date: date
    ) -> dict:
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
        dict
            Kitchen availability by day and time slot
        """
        schedules = (
            db.query(Schedule)
            .filter(
                and_(
                    Schedule.location == location,
                    Schedule.is_active == True,
                    or_(Schedule.start_date == None, Schedule.start_date <= end_date),
                    or_(Schedule.end_date == None, Schedule.end_date >= start_date),
                )
            )
            .all()
        )
        
        # Generate all days between start and end date
        days = []
        current_date = start_date
        while current_date <= end_date:
            days.append(current_date)
            current_date = current_date + timedelta(days=1)
        
        # Map each schedule to affected days
        availability = {}
        for day in days:
            day_of_week = day.weekday()
            availability[day.isoformat()] = {
                "date": day.isoformat(),
                "day_of_week": day_of_week,
                "booked_slots": [
                    {
                        "schedule_id": s.id,
                        "course_id": s.course_id,
                        "start_time": s.start_time.isoformat(),
                        "end_time": s.end_time.isoformat(),
                    }
                    for s in schedules
                    if s.day_of_week == day_of_week
                ],
            }
        
        return {
            "location": location,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_availability": availability,
        }