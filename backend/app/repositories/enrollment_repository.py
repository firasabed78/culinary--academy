"""
Objective: Implement a specialized repository for enrollment operations.
This file extends the base repository with enrollment-specific query methods,
providing functionality for managing student course enrollments and their statuses.


The EnrollmentRepository further demonstrates the repository pattern by focusing on the specific requirements of managing student enrollments in courses.
Key Features:

Enrollment Management Operations:

Student-Course Relationship: Methods for checking and retrieving enrollments by student-course pairs
Status Management: Specialized methods for updating enrollment and payment statuses
Enrollment Counting: Course enrollment count for capacity management
Multi-Entity View: Eager loading of related student, course, and payment data


Query Patterns:

Relationship-Based Queries: Finding enrollments by student or course
Status Filtering: Retrieving enrollments by various status types
Complex Filtering: Supporting multiple criteria simultaneously
List-Based Filtering: Handling arrays of course IDs for filtering


Status Tracking:

Dual Status Tracking: Separate methods for enrollment status and payment status
Enum-Based Status: Using strongly typed enums for status values
Status Transition Support: Methods specifically for status updates


Design Considerations:

Task-Oriented Methods: Methods designed around specific use cases
Type Safety: Using enums for status values to prevent errors
Performance Optimization: Strategic use of eager loading
Clear Update Patterns: Specialized update methods for specific fields



This repository effectively manages the critical enrollment relationship between students and courses, serving as the bridge between these two core entities in an educational system. The separation of enrollment status and payment status allows for granular tracking of both the administrative approval process and the financial aspects of course registration.
The repository provides all the necessary methods to support the enrollment lifecycle, from initial registration, through approval and payment, to completion, with appropriate filtering capabilities to support administrative dashboards and student portals.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships

from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment, EnrollmentCreate, EnrollmentUpdate]):
    """
    Repository for enrollment operations.
    
    Extends the base repository with enrollment-specific queries for
    retrieving, filtering, and updating student enrollments in courses.
    """
    
    def __init__(self):
        """Initialize with Enrollment model."""
        super().__init__(Enrollment)

    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """
        Get an enrollment with related data (student, course, payments).
        
        Uses eager loading to retrieve an enrollment with all its related entities
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Enrollment ID
            
        Returns:
            Enrollment with loaded relationships or None if not found
        """
        return db.query(self.model)\
            .options(
                joinedload(self.model.student),  # Load student
                joinedload(self.model.course),   # Load course
                joinedload(self.model.payments)  # Load payments
            )\
            .filter(self.model.id == id)\
            .first()

    def get_by_student_and_course(
        self, db: Session, *, student_id: int, course_id: int
    ) -> Optional[Enrollment]:
        """
        Get enrollment by student ID and course ID.
        
        Finds a specific enrollment by the combination of student and course,
        useful for checking if a student is already enrolled in a course.
        
        Args:
            db: SQLAlchemy database session
            student_id: Student ID
            course_id: Course ID
            
        Returns:
            Matching enrollment or None if not found
        """
        return db.query(self.model)\
            .filter(
                self.model.student_id == student_id,
                self.model.course_id == course_id
            )\
            .first()

    def get_by_student(self, db: Session, *, student_id: int) -> List[Enrollment]:
        """
        Get all enrollments for a student.
        
        Retrieves all courses a student is enrolled in.
        
        Args:
            db: SQLAlchemy database session
            student_id: Student ID
            
        Returns:
            List of enrollments for the specified student
        """
        return db.query(self.model)\
            .filter(self.model.student_id == student_id)\
            .all()

    def get_by_course(self, db: Session, *, course_id: int) -> List[Enrollment]:
        """
        Get all enrollments for a course.
        
        Retrieves all students enrolled in a specific course.
        
        Args:
            db: SQLAlchemy database session
            course_id: Course ID
            
        Returns:
            List of enrollments for the specified course
        """
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .all()

    def get_by_status(
        self, db: Session, *, status: EnrollmentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get enrollments by status.
        
        Retrieves enrollments with a specific status (e.g., pending, approved)
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            status: EnrollmentStatus enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of enrollments with the specified status
        """
        return db.query(self.model)\
            .filter(self.model.status == status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_payment_status(
        self, db: Session, *, payment_status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get enrollments by payment status.
        
        Retrieves enrollments with a specific payment status (e.g., paid, pending)
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            payment_status: PaymentStatus enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of enrollments with the specified payment status
        """
        return db.query(self.model)\
            .filter(self.model.payment_status == payment_status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_status(
        self, db: Session, *, db_obj: Enrollment, status: EnrollmentStatus
    ) -> Enrollment:
        """
        Update enrollment status.
        
        Updates an enrollment's status (e.g., from pending to approved)
        and persists the change to the database.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Enrollment object to update
            status: New enrollment status
            
        Returns:
            Updated enrollment object
        """
        db_obj.status = status  # Set new status
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get updated values
        return db_obj

    def update_payment_status(
        self, db: Session, *, db_obj: Enrollment, payment_status: PaymentStatus
    ) -> Enrollment:
        """
        Update enrollment payment status.
        
        Updates an enrollment's payment status (e.g., from pending to paid)
        and persists the change to the database.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Enrollment object to update
            payment_status: New payment status
            
        Returns:
            Updated enrollment object
        """
        db_obj.payment_status = payment_status  # Set new payment status
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get updated values
        return db_obj

    def get_count_by_course(self, db: Session, *, course_id: int) -> int:
        """
        Get the count of enrollments for a course.
        
        Counts how many students are enrolled in a specific course,
        useful for capacity management.
        
        Args:
            db: SQLAlchemy database session
            course_id: Course ID
            
        Returns:
            Count of enrollments for the course
        """
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .count()

    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Enrollment]:
        """
        Get enrollments with complex filtering.
        
        Applies multiple filtering conditions based on the provided
        filter parameters, supporting a wide range of query criteria.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Field name/value pairs for filtering
            
        Returns:
            List of enrollments matching the filter criteria
        """
        query = db.query(self.model)
        
        # Apply filters based on filter name and value
        for key, value in filters.items():
            if key == "student_id" and value:
                query = query.filter(self.model.student_id == value)
            elif key == "course_id" and value:
                # Handle list of course IDs
                if isinstance(value, list):
                    query = query.filter(self.model.course_id.in_(value))
                else:
                    query = query.filter(self.model.course_id == value)
            elif key == "status" and value:
                query = query.filter(self.model.status == value)
            elif key == "payment_status" and value:
                query = query.filter(self.model.payment_status == value)
        
        return query.offset(skip).limit(limit).all()