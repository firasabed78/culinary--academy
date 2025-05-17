from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class PaymentMethod(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    OTHER = "other"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    """Payment records for course enrollments."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    transaction_id = Column(String(255), nullable=True, unique=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    notes = Column(String(500), nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="payments")
    
    class Config:
        orm_mode = True