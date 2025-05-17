"""
payment.py - Payment model definition
This file defines the SQLAlchemy ORM model for payment records associated with
course enrollments. It includes enums for payment methods and statuses, tracks
payment metadata such as amount and transaction IDs, and establishes relationships
with enrollments. The payment system enables financial transactions for course
registrations and maintains an audit trail of payment activities.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Float, Enum  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
from sqlalchemy.sql import func  # Import SQL functions for default timestamps
import enum  # Import Python's enum module for type definitions
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class PaymentMethod(str, enum.Enum):
    """
    Enumeration of supported payment methods.
    Defines the various payment options available to users.
    """
    CREDIT_CARD = "credit_card"      # Credit card payments
    DEBIT_CARD = "debit_card"        # Debit card payments
    PAYPAL = "paypal"                # PayPal electronic payments
    BANK_TRANSFER = "bank_transfer"  # Direct bank transfers/wire transfers
    OTHER = "other"                  # Other payment methods not specifically categorized

class PaymentStatus(str, enum.Enum):
    """
    Enumeration of possible payment statuses.
    Tracks the state of a payment through its lifecycle.
    """
    PENDING = "pending"      # Payment initiated but not yet confirmed
    COMPLETED = "completed"  # Payment successfully processed and confirmed
    FAILED = "failed"        # Payment attempt unsuccessful
    REFUNDED = "refunded"    # Payment reversed and returned to payer

class Payment(Base):
    """Payment records for course enrollments."""
    __tablename__ = "payments"  # Database table name for payments
    
    # Primary key and relationship IDs
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)  # Foreign key to associated enrollment
    
    # Payment details
    amount = Column(Float, nullable=False)  # Payment amount in default currency
    payment_date = Column(DateTime(timezone=True), server_default=func.now())  # Automatic timestamp when payment record is created
    payment_method = Column(Enum(PaymentMethod), nullable=True)  # Method used for payment
    transaction_id = Column(String(255), nullable=True, unique=True)  # External payment processor's transaction reference
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)  # Current state of the payment
    notes = Column(String(500), nullable=True)  # Optional administrative notes about the payment
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="payments")  # Bi-directional relationship with Enrollment model
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration