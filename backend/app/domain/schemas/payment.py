"""
Objective: Define data validation and serialization models for payment resources.
This file defines the Pydantic models used for validating payment-related data
in requests and responses, ensuring type safety and data integrity.

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

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.domain.models.payment import PaymentMethod, PaymentStatus  # Import enums from SQLAlchemy model

class PaymentBase(BaseModel):
    """
    Base schema for payment data.
    
    Contains common fields that are shared across all payment schemas,
    serving as the foundation for more specific payment models.
    """
    enrollment_id: int  # The enrollment being paid for
    amount: float = Field(..., gt=0)  # Payment amount (must be positive)
    payment_method: Optional[PaymentMethod] = None  # Optional payment method
    transaction_id: Optional[str] = None  # Optional external transaction ID
    notes: Optional[str] = None  # Optional payment notes

class PaymentCreate(PaymentBase):
    """
    Schema for creating a new payment.
    
    Extends the base schema with additional fields required when creating
    a new payment, including the default payment status.
    """
    status: PaymentStatus = PaymentStatus.PENDING  # Default payment status
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        """
        Validate that payment amount is positive.
        
        This validator ensures that payment amounts are always greater than zero,
        providing meaningful error messages for invalid inputs.
        """
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class PaymentUpdate(BaseModel):
    """
    Schema for updating a payment.
    
    Contains fields that can be updated after payment creation.
    All fields are optional as updates may only change specific fields.
    """
    payment_method: Optional[PaymentMethod] = None  # Update payment method
    transaction_id: Optional[str] = None  # Update transaction ID
    status: Optional[PaymentStatus] = None  # Update payment status
    notes: Optional[str] = None  # Update notes

class PaymentInDB(PaymentBase):
    """
    Schema for payment in database.
    
    Complete payment model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    payment_date: datetime  # When the payment was made
    status: PaymentStatus  # Current payment status
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Payment(PaymentInDB):
    """
    Schema for payment API response.
    
    The primary model used for API responses containing payment data.
    Inherits all fields from PaymentInDB.
    """
    pass

class PaymentWithEnrollment(Payment):
    """
    Schema for payment with enrollment details.
    
    Extended payment model that includes the associated enrollment's information,
    typically used for detailed payment views.
    """
    from app.domain.schemas.enrollment import Enrollment  # Import needed here to avoid circular imports
    enrollment: Enrollment  # The enrollment this payment is for