from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class EnrollmentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class Enrollment(Base):
    """Student enrollment in a course."""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])
    course = relationship("Course", back_populates="enrollments")
    payments = relationship("Payment", back_populates="enrollment", cascade="all, delete-orphan")
    
    class Config:
        orm_mode = True