from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload

from app.domain.models.enrollment import Enrollment, EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import EnrollmentCreate, EnrollmentUpdate
from app.repositories.base import BaseRepository


class EnrollmentRepository(BaseRepository[Enrollment, EnrollmentCreate, EnrollmentUpdate]):
    """Repository for enrollment operations."""
    
    def __init__(self):
        super().__init__(Enrollment)

    def get_with_relations(self, db: Session, id: int) -> Optional[Enrollment]:
        """Get an enrollment with related data (student, course, payments)."""
        return db.query(self.model)\
            .options(
                joinedload(self.model.student),
                joinedload(self.model.course),
                joinedload(self.model.payments)
            )\
            .filter(self.model.id == id)\
            .first()

    def get_by_student_and_course(
        self, db: Session, *, student_id: int, course_id: int
    ) -> Optional[Enrollment]:
        """Get enrollment by student ID and course ID."""
        return db.query(self.model)\
            .filter(
                self.model.student_id == student_id,
                self.model.course_id == course_id
            )\
            .first()

    def get_by_student(self, db: Session, *, student_id: int) -> List[Enrollment]:
        """Get all enrollments for a student."""
        return db.query(self.model)\
            .filter(self.model.student_id == student_id)\
            .all()

    def get_by_course(self, db: Session, *, course_id: int) -> List[Enrollment]:
        """Get all enrollments for a course."""
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .all()

    def get_by_status(
        self, db: Session, *, status: EnrollmentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """Get enrollments by status."""
        return db.query(self.model)\
            .filter(self.model.status == status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_payment_status(
        self, db: Session, *, payment_status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Enrollment]:
        """Get enrollments by payment status."""
        return db.query(self.model)\
            .filter(self.model.payment_status == payment_status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_status(
        self, db: Session, *, db_obj: Enrollment, status: EnrollmentStatus
    ) -> Enrollment:
        """Update enrollment status."""
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_payment_status(
        self, db: Session, *, db_obj: Enrollment, payment_status: PaymentStatus
    ) -> Enrollment:
        """Update enrollment payment status."""
        db_obj.payment_status = payment_status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_count_by_course(self, db: Session, *, course_id: int) -> int:
        """Get the count of enrollments for a course."""
        return db.query(self.model)\
            .filter(self.model.course_id == course_id)\
            .count()

    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Enrollment]:
        """Get enrollments with complex filtering."""
        query = db.query(self.model)
        
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