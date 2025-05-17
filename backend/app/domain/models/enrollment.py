"""
enrollment.py - Enrollment model definition
This file defines the SQLAlchemy ORM model for student enrollments in courses.
It includes status enums for tracking enrollment and payment states, and 
establishes relationships between students, courses, and payments. The enrollment
system serves as the core connection between users and courses, tracking both
the administrative approval process and payment lifecycle.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Enum  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
from sqlalchemy.sql import func  # Import SQL functions for default timestamps
import enum  # Import Python's enum module for status definitions
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class EnrollmentStatus(str, enum.Enum):
    """
    Enumeration of possible enrollment statuses.
    Tracks the administrative state of a student's enrollment in a course.
    """
    PENDING = "pending"     # Initial state, awaiting approval
    APPROVED = "approved"   # Enrollment approved by administrator
    REJECTED = "rejected"   # Enrollment rejected by administrator
    COMPLETED = "completed" # Student has completed the course

class PaymentStatus(str, enum.Enum):
    """
    Enumeration of possible payment statuses.
    Tracks the financial state of an enrollment.
    """
    PENDING = "pending"   # Payment not yet made
    PAID = "paid"         # Payment successfully processed
    REFUNDED = "refunded" # Payment refunded to student
    FAILED = "failed"     # Payment attempt failed

class Enrollment(Base):
    """Student enrollment in a course."""
    __tablename__ = "enrollments"  # Database table name for enrollments
    
    # Primary key and relationship IDs
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Foreign key to student user
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)  # Foreign key to course
    
    # Enrollment metadata
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())  # Automatic timestamp when enrollment is created
    status = Column(Enum(EnrollmentStatus), default=EnrollmentStatus.PENDING, nullable=False)  # Administrative status of enrollment
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)  # Financial status of enrollment
    notes = Column(String(500), nullable=True)  # Optional administrative notes about the enrollment
    
    # Relationships
    student = relationship("User", back_populates="enrollments", foreign_keys=[student_id])  # Bi-directional relationship with User model
    course = relationship("Course", back_populates="enrollments")  # Bi-directional relationship with Course model
    payments = relationship("Payment", back_populates="enrollment", cascade="all, delete-orphan")  # Related payments with cascade delete
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration