from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from datetime import date

from app.domain.models.course import Course
from app.domain.schemas.course import CourseCreate, CourseUpdate
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course, CourseCreate, CourseUpdate]):
    """Repository for course operations."""
    
    def __init__(self):
        super().__init__(Course)

    def get_with_relations(self, db: Session, id: int) -> Optional[Course]:
        """Get a course with instructor, enrollments, and schedules."""
        return db.query(self.model)\
            .options(
                joinedload(self.model.instructor),
                joinedload(self.model.enrollments),
                joinedload(self.model.schedules)
            )\
            .filter(self.model.id == id)\
            .first()
    
    def get_by_title(self, db: Session, *, title: str) -> Optional[Course]:
        """Get a course by title."""
        return db.query(self.model)\
            .filter(self.model.title == title)\
            .first()
    
    def get_by_instructor(self, db: Session, *, instructor_id: int) -> List[Course]:
        """Get all courses for an instructor."""
        return db.query(self.model)\
            .filter(self.model.instructor_id == instructor_id)\
            .all()
    
    def get_active_courses(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get all active courses."""
        return db.query(self.model)\
            .filter(self.model.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """Get courses within a date range."""
        return db.query(self.model)\
            .filter(
                (self.model.start_date.is_(None) | (self.model.start_date <= end_date)),
                (self.model.end_date.is_(None) | (self.model.end_date >= start_date))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_price_range(
        self, db: Session, *, min_price: float, max_price: float, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """Get courses within a price range."""
        return db.query(self.model)\
            .filter(
                self.model.price >= min_price,
                self.model.price <= max_price
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_with_available_seats(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Course]:
        """Get courses that have available seats."""
        from sqlalchemy import func
        from app.domain.models.enrollment import Enrollment, EnrollmentStatus
        
        subquery = db.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label('enrollment_count')
        ).filter(
            Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING])
        ).group_by(Enrollment.course_id).subquery()
        
        return db.query(self.model)\
            .outerjoin(subquery, self.model.id == subquery.c.course_id)\
            .filter(
                self.model.is_active == True,
                (subquery.c.enrollment_count.is_(None) | 
                 (subquery.c.enrollment_count < self.model.capacity))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def search_courses(
        self, db: Session, *, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """Search courses by title or description."""
        search_pattern = f"%{search_term}%"
        return db.query(self.model)\
            .filter(
                (self.model.title.ilike(search_pattern) | 
                 self.model.description.ilike(search_pattern))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Course]:
        """Get courses with complex filtering."""
        query = db.query(self.model)
        
        for key, value in filters.items():
            if key == "instructor_id" and value:
                query = query.filter(self.model.instructor_id == value)
            elif key == "is_active" and value is not None:
                query = query.filter(self.model.is_active == value)
            elif key == "title" and value:
                query = query.filter(self.model.title.ilike(f"%{value}%"))
            elif key == "min_price" and value is not None:
                query = query.filter(self.model.price >= value)
            elif key == "max_price" and value is not None:
                query = query.filter(self.model.price <= value)
            elif key == "start_date_after" and value:
                query = query.filter(
                    (self.model.start_date.is_(None) | (self.model.start_date >= value))
                )
            elif key == "end_date_before" and value:
                query = query.filter(
                    (self.model.end_date.is_(None) | (self.model.end_date <= value))
                )
        
        return query.offset(skip).limit(limit).all()
    
    def get_course_stats(self, db: Session) -> Dict[str, Any]:
        """Get course statistics."""
        total = db.query(self.model).count()
        active = db.query(self.model).filter(self.model.is_active == True).count()
        
        # Get courses starting in the future
        today = date.today()
        upcoming = db.query(self.model).filter(
            self.model.start_date > today
        ).count()
        
        # Get courses that have ended
        completed = db.query(self.model).filter(
            self.model.end_date < today
        ).count()
        
        return {
            "total": total,
            "active": active,
            "upcoming": upcoming,
            "completed": completed
        }
    
    def get_course_with_enrollment_count(self, db: Session, id: int) -> Optional[Dict[str, Any]]:
        """Get a course with its enrollment count."""
        from sqlalchemy import func
        from app.domain.models.enrollment import Enrollment
        
        course = self.get(db, id)
        if not course:
            return None
        
        enrollment_count = db.query(func.count(Enrollment.id))\
            .filter(Enrollment.course_id == id)\
            .scalar()
        
        # Convert SQLAlchemy model to dict and add count
        course_dict = {c.name: getattr(course, c.name) for c in course.__table__.columns}
        course_dict["enrollment_count"] = enrollment_count
        
        return course_dict