from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from datetime import date, time

from app.domain.models.schedule import Schedule
from app.domain.schemas.schedule import ScheduleCreate, ScheduleUpdate
from app.repositories.base import BaseRepository


class ScheduleRepository(BaseRepository[Schedule, ScheduleCreate, ScheduleUpdate]):
    """Repository for schedule operations."""
    
    def __init__(self):
        super().__init__(Schedule)

    def get_with_course(self, db: Session, id: int) -> Optional[Schedule]:
        """Get a schedule with related course data."""
        return db.query(self.model)\
            .options(joinedload(self.model.course))\
            .filter(self.model.id == id)\
            .first()

    def get_by_course(self, db: Session, *, course_id: int) -> List[Schedule]:
        """Get all schedules for a course."""
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .all()

    def get_by_day_of_week(
        self, db: Session, *, day_of_week: int, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules for a specific day of the week."""
        return db.query(self.model)\
            .filter(self.model.day_of_week == day_of_week)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_active_schedules(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get all active schedules."""
        return db.query(self.model)\
            .filter(self.model.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_time_range(
        self, db: Session, *, start_time: time, end_time: time, skip: int = 0, limit: int = 100
    ) -> List[Schedule]:
        """Get schedules within a time range."""
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
        """Get schedules within a date range."""
        return db.query(self.model)\
            .filter(
                (self.model.start_date.is_(None) | (self.model.start_date <= end_date)),
                (self.model.end_date.is_(None) | (self.model.end_date >= start_date))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_overlapping_schedules(
        self, db: Session, *, day_of_week: int, start_time: time, end_time: time, 
        exclude_id: Optional[int] = None
    ) -> List[Schedule]:
        """Get schedules that overlap with the given time slot."""
        query = db.query(self.model).filter(
            self.model.day_of_week == day_of_week,
            self.model.end_time > start_time,
            self.model.start_time < end_time
        )
        
        if exclude_id:
            query = query.filter(self.model.id != exclude_id)
            
        return query.all()