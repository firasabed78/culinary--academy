"""
crud_enrollment.py - Enrollment CRUD operations
This file defines database operations for managing student enrollments in culinary
courses, including status management and filtering by various criteria.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.crud.base import CRUDBase
from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate


class CRUDEnrollment(CRUDBase[Enrollment, EnrollmentCreate, EnrollmentUpdate]):
    """CRUD operations for Enrollment model with specialized filtering methods."""
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """
        Get enrollment with student and course data joined.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Enrollment ID
        
        Returns
        -------
        Optional[Enrollment]
            Enrollment with related data if found, None otherwise
        """
        return (
            db.query(Enrollment)
            .filter(Enrollment.id == id)
            .first()
        )
    
    def get_by_student(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a specific student.
        
        Parameters
        ----------
        db: SQLAlchemy session
        student_id: ID of the student
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of student's enrollments
        """
        return (
            db.query(Enrollment)
            .filter(Enrollment.student_id == student_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_course(
        self, db: Session, *, course_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments for a specific course.
        
        Parameters
        ----------
        db: SQLAlchemy session
        course_id: ID of the course
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of course enrollments
        """
        return (
            db.query(Enrollment)
            .filter(Enrollment.course_id == course_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_status(
        self,
        db: Session,
        *,
        status: EnrollmentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments with a specific status.
        
        Parameters
        ----------
        db: SQLAlchemy session
        status: Enrollment status to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of enrollments with the specified status
        """
        return (
            db.query(Enrollment)
            .filter(Enrollment.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_payment_status(
        self,
        db: Session,
        *,
        payment_status: PaymentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Enrollment]:
        """
        Get all enrollments with a specific payment status.
        
        Parameters
        ----------
        db: SQLAlchemy session
        payment_status: Payment status to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Enrollment]
            List of enrollments with the specified payment status
        """
        return (
            db.query(Enrollment)
            .filter(Enrollment.payment_status == payment_status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def check_student_enrolled(
        self, db: Session, *, student_id: int, course_id: int
    ) -> bool:
        """
        Check if a student is already enrolled in a course.
        
        Parameters
        ----------
        db: SQLAlchemy session
        student_id: ID of the student
        course_id: ID of the course
        
        Returns
        -------
        bool
            True if student is already enrolled, False otherwise
        """
        enrollment = (
            db.query(Enrollment)
            .filter(
                and_(
                    Enrollment.student_id == student_id,
                    Enrollment.course_id == course_id,
                )
            )
            .first()
        )
        return enrollment is not None
    
    def update_status(
        self, db: Session, *, db_obj: Enrollment, status: EnrollmentStatus
    ) -> Enrollment:
        """
        Update the status of an enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        db_obj: Enrollment instance to update
        status: New enrollment status
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
        """
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update_payment_status(
        self, db: Session, *, db_obj: Enrollment, payment_status: PaymentStatus
    ) -> Enrollment:
        """
        Update the payment status of an enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        db_obj: Enrollment instance to update
        payment_status: New payment status
        
        Returns
        -------
        Enrollment
            Updated enrollment instance
        """
        db_obj.payment_status = payment_status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_enrollment_stats(self, db: Session) -> dict:
        """
        Get enrollment statistics.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        dict
            Enrollment statistics by status and payment status
        """
        total = db.query(func.count(Enrollment.id)).scalar()
        
        # Status counts
        pending = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == EnrollmentStatus.PENDING)
            .scalar()
        )
        approved = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == EnrollmentStatus.APPROVED)
            .scalar()
        )
        rejected = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == EnrollmentStatus.REJECTED)
            .scalar()
        )
        completed = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.status == EnrollmentStatus.COMPLETED)
            .scalar()
        )
        
        # Payment status counts
        payment_pending = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.payment_status == PaymentStatus.PENDING)
            .scalar()
        )
        payment_paid = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.payment_status == PaymentStatus.PAID)
            .scalar()
        )
        payment_refunded = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.payment_status == PaymentStatus.REFUNDED)
            .scalar()
        )
        payment_failed = (
            db.query(func.count(Enrollment.id))
            .filter(Enrollment.payment_status == PaymentStatus.FAILED)
            .scalar()
        )
        
        return {
            "total": total,
            "by_status": {
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "completed": completed,
            },
            "by_payment_status": {
                "pending": payment_pending,
                "paid": payment_paid,
                "refunded": payment_refunded,
                "failed": payment_failed,
            },
        }