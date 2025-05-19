"""
crud_course.py - Course CRUD operations
This file defines database operations specific to culinary course management,
including specialized methods for filtering courses by availability, difficulty,
and other culinary-specific criteria.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import CRUDBase
from app.domain.models.course import Course
from app.domain.schemas.course import CourseCreate, CourseUpdate


class CRUDCourse(CRUDBase[Course, CourseCreate, CourseUpdate]):
    """CRUD operations for Course model with culinary academy specific methods."""
    
    def get_with_instructor(self, db: Session, id: int) -> Optional[Course]:
        """
        Get a course with instructor data joined.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Course ID
        
        Returns
        -------
        Optional[Course]
            Course with instructor data if found, None otherwise
        """
        return db.query(Course).filter(Course.id == id).first()
    
    def get_available_courses(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get all active courses with available capacity.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Course]
            List of available courses
        """
        return (
            db.query(Course)
            .filter(Course.is_active == True)  # Only active courses
            .filter(Course.capacity > 0)  # With available capacity
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_instructor(
        self, db: Session, *, instructor_id: int, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get all courses taught by a specific instructor.
        
        Parameters
        ----------
        db: SQLAlchemy session
        instructor_id: ID of the instructor
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Course]
            List of courses taught by the instructor
        """
        return (
            db.query(Course)
            .filter(Course.instructor_id == instructor_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_upcoming_courses(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get all courses that have not yet started.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Course]
            List of upcoming courses
        """
        today = date.today()
        return (
            db.query(Course)
            .filter(Course.is_active == True)
            .filter(Course.start_date > today)
            .order_by(Course.start_date)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def search_courses(
        self,
        db: Session,
        *,
        keyword: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Course]:
        """
        Search for courses with various filters.
        
        Parameters
        ----------
        db: SQLAlchemy session
        keyword: Search term for title and description
        min_price: Minimum course price
        max_price: Maximum course price
        start_date: Earliest start date
        end_date: Latest end date
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Course]
            List of courses matching the search criteria
        """
        query = db.query(Course).filter(Course.is_active == True)
        
        # Apply keyword filter
        if keyword:
            search_term = f"%{keyword}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term),
                )
            )
        
        # Apply price filter
        if min_price is not None:
            query = query.filter(Course.price >= min_price)
        if max_price is not None:
            query = query.filter(Course.price <= max_price)
        
        # Apply date filters
        if start_date:
            query = query.filter(Course.start_date >= start_date)
        if end_date:
            query = query.filter(Course.end_date <= end_date)
        
        # Return results with pagination
        return query.offset(skip).limit(limit).all()
    
    def update_capacity(self, db: Session, *, course_id: int, change: int) -> Course:
        """
        Update course capacity when students enroll or unenroll.
        
        Parameters
        ----------
        db: SQLAlchemy session
        course_id: ID of the course
        change: Change in capacity (negative for enrollments, positive for cancellations)
        
        Returns
        -------
        Course
            Updated course instance
        """
        course = self.get(db, course_id)
        if course:
            # Ensure capacity doesn't go below 0
            course.capacity = max(0, course.capacity + change)
            db.add(course)
            db.commit()
            db.refresh(course)
        return course