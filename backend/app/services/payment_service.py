from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import stripe

from app.domain.models.payment import Payment, PaymentStatus
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate
from app.repositories.payment_repository import PaymentRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_API_KEY


class PaymentService(BaseService[Payment, PaymentCreate, PaymentUpdate, PaymentRepository]):
    """Service for payment operations."""
    
    def __init__(self):
        super().__init__(PaymentRepository)
        self.enrollment_repository = EnrollmentRepository()
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """Get a payment with related data."""
        payment = self.repository.get_with_relations(db, id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        return payment
    
    def create_payment(self, db: Session, *, obj_in: PaymentCreate) -> Payment:
        """Create a new payment."""
        # Check if enrollment exists
        enrollment = self.enrollment_repository.get(db, obj_in.enrollment_id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        # Create payment
        return self.repository.create(db, obj_in=obj_in)
    
    async def create_payment_intent(
        self, db: Session, *, payment_id: int, amount: float, currency: str = "usd"
    ) -> Dict[str, Any]:
        """Create a Stripe payment intent for a payment."""
        payment = self.repository.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        try:
            # Convert amount to cents for Stripe
            amount_cents = int(amount * 100)
            
            # Create a PaymentIntent with the order amount and currency
            intent = await stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata={
                    "payment_id": payment_id,
                    "enrollment_id": payment.enrollment_id
                }
            )
            
            # Update payment with transaction ID
            self.repository.update(
                db, 
                db_obj=payment, 
                obj_in={"transaction_id": intent.id}
            )
            
            return {
                "clientSecret": intent.client_secret,
                "payment_id": payment_id
            }
        except Exception as e:
            # Update payment status to failed on error
            self.repository.update_status(
                db, db_obj=payment, status=PaymentStatus.FAILED
            )
            raise ValidationError(detail=str(e))
    
    async def process_payment_webhook(
        self, db: Session, *, event_type: str, payment_intent: Dict[str, Any]
    ) -> Optional[Payment]:
        """Process a Stripe webhook event."""
        if event_type != "payment_intent.succeeded":
            return None
        
        transaction_id = payment_intent.get("id")
        if not transaction_id:
            return None
        
        # Find payment by transaction ID
        payment = self.repository.get_by_transaction_id(db, transaction_id=transaction_id)
        if not payment:
            return None
        
        # Update payment status
        payment = self.repository.update_status(
            db, db_obj=payment, status=PaymentStatus.COMPLETED
        )
        
        # Update enrollment payment status
        enrollment = self.enrollment_repository.get(db, id=payment.enrollment_id)
        if enrollment:
            self.enrollment_repository.update_payment_status(
                db, db_obj=enrollment, payment_status=PaymentStatus.PAID
            )
        
        return payment
    
    async def refund_payment(self, db: Session, *, payment_id: int) -> Payment:
        """Refund a payment via Stripe."""
        payment = self.repository.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(detail="Only completed payments can be refunded")
        
        if not payment.transaction_id:
            raise ValidationError(detail="Payment has no transaction ID")
        
        try:
            # Create Stripe refund
            refund = await stripe.Refund.create(
                payment_intent=payment.transaction_id
            )
            
            # Update payment status
            payment = self.repository.update_status(
                db, db_obj=payment, status=PaymentStatus.REFUNDED
            )
            
            # Update enrollment payment status
            enrollment = self.enrollment_repository.get(db, id=payment.enrollment_id)
            if enrollment:
                self.enrollment_repository.update_payment_status(
                    db, db_obj=enrollment, payment_status=PaymentStatus.REFUNDED
                )
            
            return payment
        except Exception as e:
            raise ValidationError(detail=f"Refund failed: {str(e)}")
    
    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """Get payment statistics."""
        return self.repository.get_payment_stats(db)