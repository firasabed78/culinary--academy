from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.domain.models.payment import PaymentMethod, PaymentStatus


class PaymentBase(BaseModel):
    """Base schema for payment data."""
    enrollment_id: int
    amount: float = Field(..., gt=0)
    payment_method: Optional[PaymentMethod] = None
    transaction_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema for creating a new payment."""
    status: PaymentStatus = PaymentStatus.PENDING

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class PaymentUpdate(BaseModel):
    """Schema for updating a payment."""
    payment_method: Optional[PaymentMethod] = None
    transaction_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class PaymentInDB(PaymentBase):
    """Schema for payment in database."""
    id: int
    payment_date: datetime
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Payment(PaymentInDB):
    """Schema for payment API response."""
    pass


class PaymentWithEnrollment(Payment):
    """Schema for payment with enrollment details."""
    from app.domain.schemas.enrollment import Enrollment

    enrollment: Enrollment