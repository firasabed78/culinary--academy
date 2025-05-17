"""
payment_service.py - Service layer for payment processing and management
This file handles business logic related to payment operations, including
integration with Stripe for payment processing, refunds, and webhook handling.
It provides an abstraction over the payment repository and manages the payment
lifecycle while coordinating with the enrollment system.
"""

from typing import List, Optional, Dict, Any  # Import common type annotations
from sqlalchemy.orm import Session  # Import SQLAlchemy session for database operations
from datetime import datetime  # Import datetime for timestamp handling
import stripe  # Import stripe SDK for payment processing

from app.domain.models.payment import Payment, PaymentStatus  # Import payment models and status enum
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate  # Import payment schemas for data validation
from app.repositories.payment_repository import PaymentRepository  # Import repository for payment DB operations
from app.repositories.enrollment_repository import EnrollmentRepository  # Import enrollment repository to update payment status
from app.services.base import BaseService  # Import base service class with common functionality
from app.core.exceptions import NotFoundError, ValidationError  # Import custom exceptions
from app.core.config import settings  # Import application settings

# Initialize Stripe API with the API key from settings
stripe.api_key = settings.STRIPE_API_KEY


class PaymentService(BaseService[Payment, PaymentCreate, PaymentUpdate, PaymentRepository]):
    """Service for payment operations."""
    
    def __init__(self):
        # Initialize with payment repository
        super().__init__(PaymentRepository)
        # Create enrollment repository instance to manage enrollment payment status
        self.enrollment_repository = EnrollmentRepository()
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """Get a payment with related data."""
        # Retrieve payment with joined relations (user, enrollment, course)
        payment = self.repository.get_with_relations(db, id)
        # Raise exception if payment not found
        if not payment:
            raise NotFoundError(detail="Payment not found")
        # Return the payment with relations data
        return payment
    
    def create_payment(self, db: Session, *, obj_in: PaymentCreate) -> Payment:
        """Create a new payment."""
        # Verify enrollment exists before creating payment
        enrollment = self.enrollment_repository.get(db, obj_in.enrollment_id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        # Create payment record in database
        return self.repository.create(db, obj_in=obj_in)
    
    async def create_payment_intent(
        self, db: Session, *, payment_id: int, amount: float, currency: str = "usd"
    ) -> Dict[str, Any]:
        """Create a Stripe payment intent for a payment."""
        # Get payment by ID
        payment = self.repository.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        try:
            # Convert amount to cents for Stripe (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            # Create a PaymentIntent with the order amount and currency
            # Stripe PaymentIntent represents the intent to collect payment from customer
            intent = await stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                metadata={
                    # Store reference IDs in metadata for webhook processing
                    "payment_id": payment_id,
                    "enrollment_id": payment.enrollment_id
                }
            )
            
            # Update payment with Stripe transaction ID for future reference
            self.repository.update(
                db, 
                db_obj=payment, 
                obj_in={"transaction_id": intent.id}
            )
            
            # Return client secret for frontend to complete payment and payment ID
            return {
                "clientSecret": intent.client_secret,
                "payment_id": payment_id
            }
        except Exception as e:
            # Update payment status to failed if Stripe operation fails
            self.repository.update_status(
                db, db_obj=payment, status=PaymentStatus.FAILED
            )
            # Raise validation error with details from Stripe exception
            raise ValidationError(detail=str(e))
    
    async def process_payment_webhook(
        self, db: Session, *, event_type: str, payment_intent: Dict[str, Any]
    ) -> Optional[Payment]:
        """Process a Stripe webhook event."""
        # Only process successful payment events
        if event_type != "payment_intent.succeeded":
            return None
        
        # Extract transaction ID from payment intent
        transaction_id = payment_intent.get("id")
        if not transaction_id:
            return None
        
        # Find payment record by Stripe transaction ID
        payment = self.repository.get_by_transaction_id(db, transaction_id=transaction_id)
        if not payment:
            return None
        
        # Update payment status to completed
        payment = self.repository.update_status(
            db, db_obj=payment, status=PaymentStatus.COMPLETED
        )
        
        # Update enrollment payment status to reflect completed payment
        enrollment = self.enrollment_repository.get(db, id=payment.enrollment_id)
        if enrollment:
            self.enrollment_repository.update_payment_status(
                db, db_obj=enrollment, payment_status=PaymentStatus.PAID
            )
        
        # Return updated payment object
        return payment
    
    async def refund_payment(self, db: Session, *, payment_id: int) -> Payment:
        """Refund a payment via Stripe."""
        # Get payment by ID
        payment = self.repository.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        # Validate payment is in completed status before refunding
        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(detail="Only completed payments can be refunded")
        
        # Ensure payment has a transaction ID to reference in Stripe
        if not payment.transaction_id:
            raise ValidationError(detail="Payment has no transaction ID")
        
        try:
            # Create Stripe refund for the payment intent
            refund = await stripe.Refund.create(
                payment_intent=payment.transaction_id
            )
            
            # Update payment status to refunded
            payment = self.repository.update_status(
                db, db_obj=payment, status=PaymentStatus.REFUNDED
            )
            
            # Update enrollment payment status to reflect refund
            enrollment = self.enrollment_repository.get(db, id=payment.enrollment_id)
            if enrollment:
                self.enrollment_repository.update_payment_status(
                    db, db_obj=enrollment, payment_status=PaymentStatus.REFUNDED
                )
            
            # Return updated payment object
            return payment
        except Exception as e:
            # Raise validation error if refund fails with Stripe error details
            raise ValidationError(detail=f"Refund failed: {str(e)}")
    
    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """Get payment statistics."""
        # Retrieve aggregated payment statistics from repository
        return self.repository.get_payment_stats(db)