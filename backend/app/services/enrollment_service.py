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
    """Service for enrollment operations."""
    
    def __init__(self):
        super().__init__(EnrollmentRepository)
        self.course_repository = CourseRepository()
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """Get an enrollment with related data."""
        enrollment = self.repository.get_with_relations(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        return enrollment
    
    def create_enrollment(self, db: Session, *, obj_in: EnrollmentCreate) -> Enrollment:
        """Create a new enrollment with validation."""
        # Check if course exists and has capacity
        course = self.course_repository.get(db, obj_in.course_id)
        if not course:
            raise NotFoundError(detail="Course not found")
        
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
        """Update enrollment status."""
        enrollment = self.repository.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        return self.repository.update_status(db, db_obj=enrollment, status=status)
    
    def update_payment_status(
        self, db: Session, *, id: int, payment_status: PaymentStatus
    ) -> Enrollment:
        """Update enrollment payment status."""
        enrollment = self.repository.get(db, id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        return self.repository.update_payment_status(db, db_obj=enrollment, payment_status=payment_status)
    
    def get_student_enrollments(
        self, db: Session, *, student_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """Get all enrollments for a student."""
        return self.repository.get_by_student(db, student_id=student_id)
    
    def get_course_enrollments(
        self, db: Session, *, course_id: int, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """Get all enrollments for a course."""
        return self.repository.get_by_course(db, course_id=course_id)
    
    def get_filtered_enrollments(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Enrollment]:
        """Get enrollments with filtering."""
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)
    
    def get_enrollment_stats(self, db: Session) -> Dict[str, Any]:
        """Get enrollment statistics."""
        total = db.query(Enrollment).count()
        pending = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.PENDING).count()
        approved = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.APPROVED).count()
        rejected = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.REJECTED).count()
        completed = db.query(Enrollment).filter(Enrollment.status == EnrollmentStatus.COMPLETED).count()
        
        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "completed": completed
        }