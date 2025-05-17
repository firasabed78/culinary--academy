"""
Objective: Implement business logic for course enrollment management.
This file provides a service layer for enrollment operations, including
validations, status updates, and statistics tracking for student enrollments.


The EnrollmentService implements the business logic for managing student enrollments in courses, providing a layer of validation and rules on top of the data access provided by the repository.
Key Features:

Enrollment Management Operations:

Enrollment Creation: With comprehensive validation rules
Status Management: Methods for updating enrollment and payment statuses
Relationship Queries: Retrieving enrollments by student or course
Filtered Queries: Complex filtering based on various criteria


Business Validations:

Course Existence: Ensuring the course exists before enrollment
Course Activity: Preventing enrollment in inactive courses
Duplicate Prevention: Checking for existing enrollments
Capacity Management: Enforcing course capacity limits


Statistical Analysis:

Status Distribution: Counting enrollments by various statuses
Aggregated Metrics: Generating enrollment statistics for dashboards


Design Patterns:

Service Layer Pattern: Encapsulating business rules separate from data access
Repository Composition: Using both enrollment and course repositories
Validation Chain: Applying multiple validation rules sequentially
Error Handling: Using custom exceptions for different error cases



Business Rules Implemented:

Course Enrollment Rules:

Students can only enroll in active courses
Students can't enroll in the same course twice
Enrollments are limited by course capacity
New enrollments start with a pending status


Status Management Rules:

Enrollment status and payment status are tracked separately
Status updates require verification of enrollment existence


Data Integrity Rules:

Relational data retrieval ensures complete information
Proper error handling for missing entities



This service demonstrates the separation of business logic from data access, showing how the service layer adds validation, rule enforcement, and cross-entity operations on top of the repositories' data access functionality.
The comprehensive validation during enrollment creation is particularly noteworthy, as it enforces multiple business rules before allowing an enrollment to be created, ensuring data integrity and business rule compliance throughout the application.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate, Enrollment as EnrollmentSchema
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.course_repository import CourseRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError


class EnrollmentService(BaseService[Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentRepository]):
    """
    Service for enrollment operations.
    
    Implements business logic for managing course enrollments,
    including creation, status updates, and data retrieval.
    """
    
    def __init__(self):
        """
        Initialize enrollment service.
        
        Sets up the enrollment repository and creates a course repository
        for course-related validation.
        """
        super().__init__(EnrollmentRepository)
        self.course_repository = CourseRepository()  # For course validation
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """
        Get an enrollment with related data.
        
        Retrieves an enrollment record with its related student, course, and payment data,
        raising an error if not found.
        
        Args:
            db: SQLAlchemy database session
            id: Enrollment ID
            
        Returns:
            Enrollment with all related data
            
        Raises:
            NotFoundError: If enrollment doesn't exist
        """
        enrollment = self.repository.get_with_relations(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        return enrollment
    
    def create_enrollment(self, db: Session, *, obj_in: EnrollmentCreate) -> Enrollment:
        """
        Create a new enrollment with validation.
        
        Creates a new enrollment after validating course existence, activity status,
        unique enrollment constraint, and course capacity.
        
        Args:
            db: SQLAlchemy database session
            obj_in: Enrollment creation data
            
        Returns:
            Created enrollment
            
        Raises:
            NotFoundError: If course doesn't exist
            ValidationError: If enrollment validation fails
        """
        # Check if course exists and has capacity
        course = self.course_repository.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check if course is active
        if not course.is_active:
            raise ValidationError(detail="Cannot enroll in inactive course")
        
        # Check if enrollment already exists
        existing_enrollment = self.repository.get_by_student_and_course(
            db, student_id=obj_in.student_id, course_id=obj_in.course_id
        )
        if existing_enrollment:
            raise ValidationError(detail="Student is already enrolled in this course")
        
        # Check if course has reached capacity
        enrollment_count = self.repository.get_count_by_course(db, course_id=obj_in.course_id)
        if enrollment_count >= course.capacity:
            raise ValidationError(detail="Course has reached maximum capacity")
        
        # Create enrollment
        return self.repository.create(db, obj_in=obj_in)
    
    def update_status(
        self, db: Session, *, id: int, status: EnrollmentStatus
    ) -> Enrollment:
        """
        Update enrollment status.
        
        Changes an enrollment's status (e.g., from pending to approved),
        raising an error if the enrollment doesn't exist.
        
        Args:
            db: SQLAlchemy database session
            id: Enrollment ID
            status: New enrollment status
            
        Returns:
            Updated enrollment
            
        Raises:
            NotFoundError: If enrollment doesn't exist
        """
        enrollment = self.repository.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        return self.repository.update_status(db, db_obj=enrollment, status=status)
    
    def update_payment_status(
        self, db: Session, *, id: int, payment_status: PaymentStatus
    ) -> Enrollment:
        """
        Update enrollment payment status.
        
        Changes an enrollment's payment status (e.g., from pending to paid),
        raising an error if the enrollment doesn't exist.
        
        Args:
            db: SQLAlchemy database session
            id: Enrollment ID
            payment_status: New payment status
            
        Returns:
            Updated enrollment
            
        Raises:
            NotFoundError: If enrollment doesn't exist
        """
        enrollment = self.repository.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        return self.repository.update_payment_status(db, db_obj=enrollment, payment_status=payment_status)
    
    def get_student_enrollments(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a student.
        
        Retrieves all courses that a specific student is enrolled in.
        
        Args:
            db: SQLAlchemy database session
            student_id: Student ID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of enrollments for the student
        """
        return self.repository.get_by_student(db, student_id=student_id)
    
    def get_course_enrollments(
        self, db: Session, *, course_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a course.
        
        Retrieves all students enrolled in a specific course.
        
        Args:
            db: SQLAlchemy database session
            course_id: Course ID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of enrollments for the course
        """
        return self.repository.get_by_course(db, course_id=course_id)
    
    def get_filtered_enrollments(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Enrollment]:
        """
        Get enrollments with filtering.
        
        Retrieves enrollments matching various filter criteria with pagination.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Filter criteria
            
        Returns:
            List of enrollments matching the filter criteria
        """
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)
    
    def get_enrollment_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get enrollment statistics.
        
        Aggregates statistics about enrollments, including counts by status.
        
        Args:
            db: SQLAlchemy database session
            
        Returns:
            Dictionary of enrollment statistics
        """
        # Count total enrollments
        total = db.query(Enrollment).count()
        
        # Count enrollments by status
        pending = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.PENDING).count()
        approved = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.APPROVED).count()
        rejected = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.REJECTED).count()
        completed = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.COMPLETED).count()
        
        # Return consolidated statistics
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "completed": completed
        }