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
"""
enrollment_service.py - Service layer for enrollment management
This file handles business logic related to student enrollments in culinary
courses, including enrollment processing, status management, and capacity tracking.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.crud import enrollment as crud_enrollment
from app.crud import course as crud_course
from app.crud import user as crud_user
from app.core.exceptions import NotFoundError, ValidationError


class EnrollmentService:
    """Service for enrollment operations using CRUD abstractions."""
    
    def get(self, db: Session, id: int) -> Optional[Enrollment]:
        """
        Get an enrollment by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Optional[Enrollment]
            Enrollment if found, None otherwise
        """
        return crud_enrollment.get(db, id)
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """
        Get an enrollment with related data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Optional[Enrollment]
            Enrollment with relations if found
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        """
        enrollment = crud_enrollment.get_with_relations(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        return enrollment
    
    def create_enrollment(self, db: Session, *, obj_in: EnrollmentCreate) -> Enrollment:
        """
        Create a new enrollment with validation.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Enrollment creation data
        
        Returns
        -------
        Enrollment
            Created enrollment instance
            
        Raises
        ------
        NotFoundError
            If student or course not found
        ValidationError
            If enrollment conditions not met
        """
        # Check if student exists
        student = crud_user.get(db, obj_in.student_id)
        if not student:
            raise NotFoundError(detail="Student not found")
        
        # Validate student role
        if not crud_user.is_student(student):
            raise ValidationError(detail="User is not a student")
        
        # Check if course exists
        course = crud_course.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
        # Check if course is active
        if not course.is_active:
            raise ValidationError(detail="Course is not active")
        
        # Check if student is already enrolled
        existing_enrollment = crud_enrollment.check_student_enrolled(
            db, student_id=obj_in.student_id, course_id=obj_in.course_id
        )
        if existing_enrollment:
            raise ValidationError(detail="Student is already enrolled in this course")
        
        # Check if course has capacity
        if course.capacity <= 0:
            raise ValidationError(detail="Course is full")
        
        # Create enrollment
        enrollment = crud_enrollment.create(db, obj_in=obj_in)
        
        # Update course capacity
        crud_course.update_capacity(db, course_id=obj_in.course_id, change=-1)
        
        return enrollment
    
    def update_enrollment(
        self, db: Session, *, id: int, obj_in: EnrollmentUpdate
    ) -> Enrollment:
        """
        Update an enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        obj_in: Update data
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        """
        enrollment = crud_enrollment.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        return crud_enrollment.update(db, db_obj=enrollment, obj_in=obj_in)
    
    def approve_enrollment(self, db: Session, *, id: int) -> Enrollment:
        """
        Approve an enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        ValidationError
            If enrollment is not in pending status
        """
        enrollment = crud_enrollment.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.PENDING:
            raise ValidationError(detail="Only pending enrollments can be approved")
        
        return crud_enrollment.update_status(db, db_obj=enrollment, status=EnrollmentStatus.APPROVED)
    
    def reject_enrollment(self, db: Session, *, id: int, reason: str = None) -> Enrollment:
        """
        Reject an enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        reason: Rejection reason (optional)
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        ValidationError
            If enrollment is not in pending status
        """
        enrollment = crud_enrollment.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.PENDING:
            raise ValidationError(detail="Only pending enrollments can be rejected")
        
        # Update status and optionally add rejection reason to notes
        enrollment = crud_enrollment.update_status(db, db_obj=enrollment, status=EnrollmentStatus.REJECTED)
        
        if reason:
            notes = f"{enrollment.notes}\nRejection reason: {reason}" if enrollment.notes else f"Rejection reason: {reason}"
            enrollment = crud_enrollment.update(db, db_obj=enrollment, obj_in={"notes": notes})
        
        # Restore course capacity
        crud_course.update_capacity(db, course_id=enrollment.course_id, change=1)
        
        return enrollment
    
    def cancel_enrollment(self, db: Session, *, id: int) -> Enrollment:
        """
        Cancel an enrollment (student initiated).
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        ValidationError
            If enrollment cannot be cancelled
        """
        enrollment = crud_enrollment.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        if enrollment.status in [EnrollmentStatus.COMPLETED, EnrollmentStatus.REJECTED]:
            raise ValidationError(detail="Cannot cancel completed or rejected enrollments")
        
        # Update status to rejected (cancelled by student)
        enrollment = crud_enrollment.update_status(db, db_obj=enrollment, status=EnrollmentStatus.REJECTED)
        
        # Restore course capacity
        crud_course.update_capacity(db, course_id=enrollment.course_id, change=1)
        
        return enrollment
    
    def complete_enrollment(self, db: Session, *, id: int) -> Enrollment:
        """
        Mark an enrollment as completed.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        ValidationError
            If enrollment is not approved
        """
        enrollment = crud_enrollment.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        if enrollment.status != EnrollmentStatus.APPROVED:
            raise ValidationError(detail="Only approved enrollments can be completed")
        
        return crud_enrollment.update_status(db, db_obj=enrollment, status=EnrollmentStatus.COMPLETED)
    
    def get_student_enrollments(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a student.
        
        Parameters
        ----------
        db: SQLAlchemy session
        student_id: Student ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of student enrollments
        """
        return crud_enrollment.get_by_student(db, student_id=student_id, skip=skip, limit=limit)
    
    def get_course_enrollments(
        self, db: Session, *, course_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a course.
        
        Parameters
        ----------
        db: SQLAlchemy session
        course_id: Course ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of course enrollments
        """
        return crud_enrollment.get_by_course(db, course_id=course_id, skip=skip, limit=limit)
    
    def get_enrollments_by_status(
        self, db: Session, *, status: EnrollmentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get enrollments by status.
        
        Parameters
        ----------
        db: SQLAlchemy session
        status: Enrollment status
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of enrollments with specified status
        """
        return crud_enrollment.get_by_status(db, status=status, skip=skip, limit=limit)
    
    def get_enrollments_by_payment_status(
        self, db: Session, *, payment_status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get enrollments by payment status.
        
        Parameters
        ----------
        db: SQLAlchemy session
        payment_status: Payment status
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of enrollments with specified payment status
        """
        return crud_enrollment.get_by_payment_status(db, payment_status=payment_status, skip=skip, limit=limit)
    
    def get_enrollment_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get enrollment statistics.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        Dict[str, Any]
            Enrollment statistics by status and payment status
        """
        return crud_enrollment.get_enrollment_stats(db)