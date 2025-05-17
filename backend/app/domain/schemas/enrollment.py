from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.domain.models.enrollment import EnrollmentStatus, PaymentStatus


class EnrollmentBase(BaseModel):
    """Base schema for enrollment data."""
    student_id: int
    course_id: int
    notes: Optional[str] = None


class EnrollmentCreate(EnrollmentBase):
    """Schema for creating a new enrollment."""
    status: EnrollmentStatus = EnrollmentStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING


class EnrollmentUpdate(BaseModel):
    """Schema for updating an enrollment."""
    status: Optional[EnrollmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class EnrollmentInDB(EnrollmentBase):
    """Schema for enrollment in database."""
    id: int
    enrollment_date: datetime
    status: EnrollmentStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Enrollment(EnrollmentInDB):
    """Schema for enrollment API response."""
    pass


class EnrollmentWithDetails(Enrollment):
    """Schema for enrollment with related data."""
    from app.domain.schemas.user import User
    from app.domain.schemas.course import Course
    from app.domain.schemas.payment import Payment

    student: User
    course: Course
    payments: List[Payment] = []