"""
crud_payment.py - Payment CRUD operations
This file defines database operations for managing payments related to culinary
course enrollments, including payment processing, refunds, and financial reporting.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.crud.base import CRUDBase
from app.domain.models.payment import Payment, PaymentStatus, PaymentMethod
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate


class CRUDPayment(CRUDBase[Payment, PaymentCreate, PaymentUpdate]):
    """CRUD operations for Payment model with financial reporting capabilities."""
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """
        Get payment with enrollment and related data joined.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Payment ID
        
        Returns
        -------
        Optional[Payment]
            Payment with related data if found, None otherwise
        """
        return (
            db.query(Payment)
            .filter(Payment.id == id)
            .first()
        )
    
    def get_by_enrollment(
        self, db: Session, *, enrollment_id: int
    ) -> List[Payment]:
        """
        Get all payments for a specific enrollment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        enrollment_id: ID of the enrollment
        
        Returns
        -------
        List[Payment]
            List of payments for the enrollment
        """
        return (
            db.query(Payment)
            .filter(Payment.enrollment_id == enrollment_id)
            .all()
        )
    
    def get_by_transaction_id(
        self, db: Session, *, transaction_id: str
    ) -> Optional[Payment]:
        """
        Get payment by external transaction ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        transaction_id: External payment processor transaction ID
        
        Returns
        -------
        Optional[Payment]
            Payment if found, None otherwise
        """
        return (
            db.query(Payment)
            .filter(Payment.transaction_id == transaction_id)
            .first()
        )
    
    def get_by_status(
        self,
        db: Session,
        *,
        status: PaymentStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Payment]:
        """
        Get all payments with a specific status.
        
        Parameters
        ----------
        db: SQLAlchemy session
        status: Payment status to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Payment]
            List of payments with the specified status
        """
        return (
            db.query(Payment)
            .filter(Payment.status == status)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_payments(
        self, db: Session, *, days: int = 30, limit: int = 100
    ) -> List[Payment]:
        """
        Get recent payments within a specified number of days.
        
        Parameters
        ----------
        db: SQLAlchemy session
        days: Number of days to look back
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Payment]
            List of recent payments
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        return (
            db.query(Payment)
            .filter(Payment.payment_date >= cutoff_date)
            .order_by(desc(Payment.payment_date))
            .limit(limit)
            .all()
        )
    
    def update_status(
        self, db: Session, *, db_obj: Payment, status: PaymentStatus
    ) -> Payment:
        """
        Update the status of a payment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        db_obj: Payment instance to update
        status: New payment status
        
        Returns
        -------
        Payment
            Updated payment instance
        """
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get payment statistics and financial summary.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        Dict[str, Any]
            Payment statistics and financial metrics
        """
        # Total counts by status
        total = db.query(func.count(Payment.id)).scalar()
        completed = (
            db.query(func.count(Payment.id))
            .filter(Payment.status == PaymentStatus.COMPLETED)
            .scalar()
        )
        pending = (
            db.query(func.count(Payment.id))
            .filter(Payment.status == PaymentStatus.PENDING)
            .scalar()
        )
        failed = (
            db.query(func.count(Payment.id))
            .filter(Payment.status == PaymentStatus.FAILED)
            .scalar()
        )
        refunded = (
            db.query(func.count(Payment.id))
            .filter(Payment.status == PaymentStatus.REFUNDED)
            .scalar()
        )
        
        # Total amounts by status
        total_amount = (
            db.query(func.sum(Payment.amount))
            .scalar() or 0
        )
        completed_amount = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.status == PaymentStatus.COMPLETED)
            .scalar() or 0
        )
        refunded_amount = (
            db.query(func.sum(Payment.amount))
            .filter(Payment.status == PaymentStatus.REFUNDED)
            .scalar() or 0
        )
        
        # Net revenue (completed - refunded)
        net_revenue = completed_amount - refunded_amount
        
        # Count by payment method
        credit_card = (
            db.query(func.count(Payment.id))
            .filter(Payment.payment_method == PaymentMethod.CREDIT_CARD)
            .scalar()
        )
        debit_card = (
            db.query(func.count(Payment.id))
            .filter(Payment.payment_method == PaymentMethod.DEBIT_CARD)
            .scalar()
        )
        paypal = (
            db.query(func.count(Payment.id))
            .filter(Payment.payment_method == PaymentMethod.PAYPAL)
            .scalar()
        )
        bank_transfer = (
            db.query(func.count(Payment.id))
            .filter(Payment.payment_method == PaymentMethod.BANK_TRANSFER)
            .scalar()
        )
        other = (
            db.query(func.count(Payment.id))
            .filter(Payment.payment_method == PaymentMethod.OTHER)
            .scalar()
        )
        
        return {
            "counts": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "failed": failed,
                "refunded": refunded,
            },
            "amounts": {
                "total": float(total_amount),
                "completed": float(completed_amount),
                "refunded": float(refunded_amount),
                "net_revenue": float(net_revenue),
            },
            "by_method": {
                "credit_card": credit_card,
                "debit_card": debit_card,
                "paypal": paypal,
                "bank_transfer": bank_transfer,
                "other": other,
            },
        }