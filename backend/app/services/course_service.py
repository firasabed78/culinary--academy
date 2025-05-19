"""
course_service.py - Service layer for culinary course management
This file provides business logic for course operations in the Culinary Academy
Student Registration system, including course creation, search, and enrollment management.
"""

from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from app.domain.models.course import Course
from app.domain.schemas.course import CourseCreate, CourseUpdate
from app.crud import course as crud_course
from app.crud import user as crud_user
from app.core.exceptions import NotFoundError, ValidationError


class CourseService:
    """Service for culinary course operations using CRUD abstractions."""
    
    def get(self, db: Session, id: int) -> Optional[Course]:
        """
        Get a course by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Course ID
        
        Returns
        -------
        Optional[Course]
            Course if found, None otherwise
        """
        return crud_course.get(db, id)
    
    def get_with_instructor(self, db: Session, id: int) -> Optional[Course]:
        """
        Get a course with instructor data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Course ID
        
        Returns
        -------
        Optional[Course]
            Course with instructor data if found, None otherwise
            
        Raises
        ------
        NotFoundError
            If course not found
        """
        course = crud_course.get_with_instructor(db, id)
        if not course:
            raise NotFoundError(detail="Course not found")
        return course
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Course]:
        """
        Get multiple courses with pagination.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Course]
            List of courses
        """
        return crud_course.get_multi(db, skip=skip, limit=limit)
    
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
        return crud_course.get_available_courses(db, skip=skip, limit=limit)
    
    def create_course(self, db: Session, *, obj_in: CourseCreate) -> Course:
        """
        Create a new course with instructor validation.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Course creation data
        
        Returns
        -------
        Course
            Created course instance
            
        Raises
        ------
        NotFoundError
            If instructor not found
        ValidationError
            If course dates are invalid
        """
        # Validate instructor exists if provided
        if obj_in.instructor_id:
            instructor = crud_user.get(db, obj_in.instructor_id)
            if not instructor:
                raise NotFoundError(detail="Instructor not found")
            
            # Validate instructor role
            if not crud_user.is_instructor(instructor):
                raise ValidationError(detail="User is not an instructor")
        
        # Validate course dates if provided
        if obj_in.start_date and obj_in.end_date and obj_in.start_date > obj_in.end_date:
            raise ValidationError(detail="End date must be after start date")
        
        return crud_course.create(db, obj_in=obj_in)
    
    def update_course(
        self, db: Session, *, id: int, obj_in: CourseUpdate
    ) -> Course:
        """
        Update a course with validation.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Course ID
        obj_in: Update data
        
        Returns
        -------
        Course
            Updated course instance
            
        Raises
        ------
        NotFoundError
            If course or instructor not found
        ValidationError
            If course dates are invalid
        """
        course = crud_course.get(db, id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Validate instructor exists if provided
        if obj_in.instructor_id:
            instructor = crud_user.get(db, obj_in.instructor_id)
            if not instructor:
                raise NotFoundError(detail="Instructor not found")
            
            # Validate instructor role
            if not crud_user.is_instructor(instructor):
                raise ValidationError(detail="User is not an instructor")
        
        # Validate course dates if provided
        start_date = obj_in.start_date if obj_in.start_date is not None else course.start_date
        end_date = obj_in.end_date if obj_in.end_date is not None else course.end_date
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError(detail="End date must be after start date")
        
        return crud_course.update(db, db_obj=course, obj_in=obj_in)
    
    def get_instructor_courses(
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
            
        Raises
        ------
        NotFoundError
            If instructor not found
        """
        instructor = crud_user.get(db, instructor_id)
        if not instructor:
            raise NotFoundError(detail="Instructor not found")
        
        if not crud_user.is_instructor(instructor):
            raise ValidationError(detail="User is not an instructor")
        
        return crud_course.get_by_instructor(db, instructor_id=instructor_id, skip=skip, limit=limit)
    
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
        return crud_course.get_upcoming_courses(db, skip=skip, limit=limit)
    
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
        return crud_course.search_courses(
            db,
            keyword=keyword,
            min_price=min_price,
            max_price=max_price,
            start_date=start_date,
            end_date=end_date,
            skip=skip,
            limit=limit,
        )
    
    def update_capacity(
        self, db: Session, *, course_id: int, change: int
    ) -> Course:
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
            
        Raises
        ------
        NotFoundError
            If course not found
        ValidationError
            If insufficient capacity for enrollment
        """
        course = crud_course.get(db, course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check if we're trying to enroll (negative change) and there's enough capacity
        if change < 0 and course.capacity + change < 0:
            raise ValidationError(detail="Insufficient course capacity")
        
        return crud_course.update_capacity(db, course_id=course_id, change=change)