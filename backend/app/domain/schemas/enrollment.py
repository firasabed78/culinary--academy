"""
Objective: Define data validation and serialization models for enrollment resources.
This file defines the Pydantic models used for validating enrollment-related data
in requests and responses, ensuring type safety and data integrity.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from app.domain.models.enrollment import EnrollmentStatus, PaymentStatus  # Import enums from SQLAlchemy model

class EnrollmentBase(BaseModel):
    """
    Base schema for enrollment data.
    
    Contains common fields that are shared across all enrollment schemas,
    serving as the foundation for more specific enrollment models.
    """
    student_id: int  # The student being enrolled
    course_id: int  # The course being enrolled in
    notes: Optional[str] = None  # Optional notes about the enrollment

class EnrollmentCreate(EnrollmentBase):
    """
    Schema for creating a new enrollment.
    
    Extends the base schema with additional fields required when creating
    a new enrollment, including default status values.
    """
    status: EnrollmentStatus = EnrollmentStatus.PENDING  # Default enrollment status
    payment_status: PaymentStatus = PaymentStatus.PENDING  # Default payment status

class EnrollmentUpdate(BaseModel):
    """
    Schema for updating an enrollment.
    
    Contains fields that can be updated after enrollment creation.
    All fields are optional as updates may only change specific fields.
    """
    status: Optional[EnrollmentStatus] = None  # New enrollment status
    payment_status: Optional[PaymentStatus] = None  # New payment status
    notes: Optional[str] = None  # New notes

class EnrollmentInDB(EnrollmentBase):
    """
    Schema for enrollment in database.
    
    Complete enrollment model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    enrollment_date: datetime  # When the enrollment was created
    status: EnrollmentStatus  # Current enrollment status
    payment_status: PaymentStatus  # Current payment status
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Enrollment(EnrollmentInDB):
    """
    Schema for enrollment API response.
    
    The primary model used for API responses containing enrollment data.
    Inherits all fields from EnrollmentInDB.
    
    These schema files define the data validation and serialization models used throughout the application. Key features include:

Type Safety: Using Python type hints and Pydantic's validation system to ensure data integrity.
Validation Rules: Fields have constraints like minimum/maximum lengths and custom validators.
Schema Organization:

Base models define common fields shared across schemas
Create models extend base models with fields needed for creation
Update models contain optional fields for partial updates
InDB models represent complete database records including auto-generated fields
Response models define what's returned in API responses


Circular Import Handling: Imports that would cause circular dependencies are done within class definitions rather than at the module level.
ORM Integration: orm_mode = True enables seamless conversion between SQLAlchemy models and Pydantic schemas.
Related Data Models: Extended schemas like WithUser or WithDetails include related entity data for comprehensive API responses.

This approach ensures consistent data validation, clear API contracts, and a clean separation between database models and API representations, all while maintaining type safety throughout the application.
    """
    pass

class EnrollmentWithDetails(Enrollment):
    """
    Schema for enrollment with related data.
    
    Extended enrollment model that includes related entities like
    student, course, and payment information, typically used for
    detailed enrollment views.
    """
    from app.domain.schemas.user import User  # Import needed here to avoid circular imports
    from app.domain.schemas.course import Course  # Import needed here to avoid circular imports
    from app.domain.schemas.payment import Payment  # Import needed here to avoid circular imports
    
    student: User  # The enrolled student
    course: Course  # The course enrolled in
    payments: List[Payment] = []  # Payments associated with this enrollment