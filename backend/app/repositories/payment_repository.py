from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.domain.models.payment import Payment, PaymentStatus
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment, PaymentCreate, PaymentUpdate]):
    """Repository for payment operations."""
    
    def __init__(self):
        super().__init__(Payment)

    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """Get a payment with related enrollment data."""
        return db.query(self.model)\
            .options(joinedload(self.model.enrollment))\
            .filter(self.model.id == id)\
            .first()

    def get_by_transaction_id(self, db: Session, *, transaction_id: str) -> Optional[Payment]:
        """Get payment by transaction ID."""
        return db.query(self.model)\
            .filter(self.model.transaction_id == transaction_id)\
            .first()

    def get_by_enrollment(self, db: Session, *, enrollment_id: int) -> List[Payment]:
        """Get all payments for an enrollment."""
        return db.query(self.model)\
            .filter(self.model.enrollment_id == enrollment_id)\
            .all()

    def get_by_status(
        self, db: Session, *, status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """Get payments by status."""
        return db.query(self.model)\
            .filter(self.model.status == status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_status(
        self, db: Session, *, db_obj: Payment, status: PaymentStatus
    ) -> Payment:
        """Update payment status."""
        db_obj.status = status
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_payments_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime
    ) -> List[Payment]:
        """Get payments within a date range."""
        return db.query(self.model)\
            .filter(
                self.model.payment_date >= start_date,
                self.model.payment_date <= end_date
            )\
            .all()

    def get_total_amount(self, db: Session) -> float:
        """Get total amount of all completed payments."""
        result = db.query(
            db.func.sum(self.model.amount)
        ).filter(
            self.model.status == PaymentStatus.COMPLETED
        ).scalar()
        return float(result) if result else 0.0

    def get_total_amount_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime
    ) -> float:
        """Get total amount of completed payments within a date range."""
        result = db.query(
            db.func.sum(self.model.amount)
        ).filter(
            self.model.payment_date >= start_date,
            self.model.payment_date <= end_date,
            self.model.status == PaymentStatus.COMPLETED
        ).scalar()
        return float(result) if result else 0.0

    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """Get payment statistics."""
        total_payments = db.query(self.model).count()
        total_amount = self.get_total_amount(db)
        
        completed_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.COMPLETED)\
            .count()
        
        pending_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.PENDING)\
            .count()
        
        failed_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.FAILED)\
            .count()
        
        return {
            "total": total_payments,
            "totalAmount": total_amount,
            "completed": completed_payments,
            "pending": pending_payments,
            "failed": failed_payments
        }