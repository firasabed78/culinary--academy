"""
Objective: Implement a specialized repository for course operations.
This file extends the base repository with course-specific query methods,
providing advanced filtering, search, and data aggregation capabilities.

The CourseRepository is an excellent example of extending the base repository pattern with domain-specific query methods. This implementation showcases how your architecture supports both common CRUD operations (inherited from BaseRepository) and specialized queries tailored to the course domain.
Key Features:

Advanced Query Methods:

Relationship Loading: get_with_relations() eagerly loads related data for efficiency
Search: search_courses() performs text search across multiple fields
Complex Filtering: get_multi_by_filters() supports numerous filtering criteria
Date Range: get_by_date_range() handles course scheduling overlaps
Capacity Management: get_with_available_seats() finds courses with open spots


SQL Techniques:

Subqueries: Used for enrollment counting and availability checks
Eager Loading: Optimizes database access with joinedload
Aggregate Functions: Counts and statistics
NULL Handling: Proper handling of optional dates with .is_(None)
Text Search: Case-insensitive with ilike()


Domain-Specific Features:

Date-Aware Queries: Finding upcoming and completed courses
Statistical Methods: get_course_stats() for dashboard metrics
Price Range Filtering: Supporting price-based search
Instructor-Based Access: Filtering by instructor for permission controls


Data Access Patterns:

Query Composition: Building complex queries incrementally
Dictionary Conversion: Converting ORM objects to dictionaries with additional data
Pagination Support: Consistent skip and limit parameters



This repository demonstrates a high level of sophistication in database access patterns while maintaining a clean, consistent API. The specialized methods reflect the unique requirements of course management in your culinary academy application, particularly with respect to scheduling, enrollment management, and instructor assignment.
The repository effectively encapsulates complex SQL queries behind an intuitive interface, making it easy for service-layer code to access exactly the data it needs without worrying about the underlying database structure or query optimization.

"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships
from datetime import date

from app.domain.models.course import Course
from app.domain.schemas.course import CourseCreate, CourseUpdate
from app.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course, CourseCreate, CourseUpdate]):
    """
    Repository for course operations.
    
    Extends the base repository with course-specific queries and data retrieval methods,
    providing advanced functionality for working with course data.
    """
    
    def __init__(self):
        """Initialize with Course model."""
        super().__init__(Course)

    def get_with_relations(self, db: Session, id: int) -> Optional[Course]:
        """
        Get a course with instructor, enrollments, and schedules.
        
        Uses eager loading to retrieve a course with all its related entities
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Course ID
            
        Returns:
            Course with loaded relationships or None if not found
        """
        return db.query(self.model)\
            .options(
                joinedload(self.model.instructor),  # Load instructor
                joinedload(self.model.enrollments),  # Load enrollments
                joinedload(self.model.schedules)    # Load schedules
            )\
            .filter(self.model.id == id)\
            .first()
    
    def get_by_title(self, db: Session, *, title: str) -> Optional[Course]:
        """
        Get a course by title.
        
        Args:
            db: SQLAlchemy database session
            title: Exact course title to match
            
        Returns:
            Matching course or None if not found
        """
        return db.query(self.model)\
            .filter(self.model.title == title)\
            .first()
    
    def get_by_instructor(self, db: Session, *, instructor_id: int) -> List[Course]:
        """
        Get all courses for an instructor.
        
        Args:
            db: SQLAlchemy database session
            instructor_id: ID of the instructor
            
        Returns:
            List of courses taught by the specified instructor
        """
        return db.query(self.model)\
            .filter(self.model.instructor_id == instructor_id)\
            .all()
    
    def get_active_courses(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Course]:
        """
        Get all active courses.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of active courses
        """
        return db.query(self.model)\
            .filter(self.model.is_active == True)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_date_range(
        self, db: Session, *, start_date: date, end_date: date, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get courses within a date range.
        
        Finds courses that overlap with the specified date range, handling courses
        with no start or end dates appropriately.
        
        Args:
            db: SQLAlchemy database session
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of courses that overlap with the date range
        """
        return db.query(self.model)\
            .filter(
                # Course starts before or on the end_date (or has no start date)
                (self.model.start_date.is_(None) | (self.model.start_date <= end_date)),
                # Course ends after or on the start_date (or has no end date)
                (self.model.end_date.is_(None) | (self.model.end_date >= start_date))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_price_range(
        self, db: Session, *, min_price: float, max_price: float, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get courses within a price range.
        
        Args:
            db: SQLAlchemy database session
            min_price: Minimum price
            max_price: Maximum price
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of courses within the price range
        """
        return db.query(self.model)\
            .filter(
                self.model.price >= min_price,
                self.model.price <= max_price
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_with_available_seats(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Course]:
        """
        Get courses that have available seats.
        
        Uses a subquery to count enrollments for each course and compares
        against the course capacity to find courses with open seats.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of courses that have seats available
        """
        from sqlalchemy import func
        from app.domain.models.enrollment import Enrollment, EnrollmentStatus
        
        # Subquery to count active enrollments by course
        subquery = db.query(
            Enrollment.course_id,
            func.count(Enrollment.id).label('enrollment_count')
        ).filter(
            # Only count pending or approved enrollments
            Enrollment.status.in_([EnrollmentStatus.APPROVED, EnrollmentStatus.PENDING])
        ).group_by(Enrollment.course_id).subquery()
        
        return db.query(self.model)\
            .outerjoin(subquery, self.model.id == subquery.c.course_id)\
            .filter(
                self.model.is_active == True,
                # Either no enrollments or fewer enrollments than capacity
                (subquery.c.enrollment_count.is_(None) | 
                 (subquery.c.enrollment_count < self.model.capacity))
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def search_courses(
        self, db: Session, *, search