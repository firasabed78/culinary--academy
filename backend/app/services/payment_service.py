"""
payment_service.py - Service layer for payment processing and management
This file handles business logic related to payment operations, including
integration with Stripe for payment processing, refunds, and webhook handling.
It provides an abstraction over the payment repository and manages the payment
lifecycle while coordinating with the enrollment system.
"""
"""
payment_service.py - Service layer for payment processing and management
This file handles business logic related to payment operations, including
integration with Stripe for payment processing, refunds, and webhook handling.
It provides an abstraction over the payment CRUD and manages the payment
lifecycle while coordinating with the enrollment system.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import stripe

from app.domain.models.payment import Payment, PaymentStatus
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate
from app.crud import payment as crud_payment
from app.crud import enrollment as crud_enrollment
from app.core.exceptions import NotFoundError, ValidationError
from app.core.config import settings

# Initialize Stripe API with the API key from settings
stripe.api_key = settings.STRIPE_API_KEY


class PaymentService:
    """Service for payment operations using CRUD abstractions."""
    
    def get(self, db: Session, id: int) -> Optional[Payment]:
        """
        Get a payment by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Payment ID
        
        Returns
        -------
        Optional[Payment]
            Payment if found, None otherwise
        """
        return crud_payment.get(db, id)
    
    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """
        Get a payment with related data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Payment ID
        
        Returns
        -------
        Optional[Payment]
            Payment with relations if found
            
        Raises
        ------
        NotFoundError
            If payment not found
        """
        payment = crud_payment.get_with_relations(db, id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        return payment
    
    def create_payment(self, db: Session, *, obj_in: PaymentCreate) -> Payment:
        """
        Create a new payment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Payment creation data
        
        Returns
        -------
        Payment
            Created payment instance
            
        Raises
        ------
        NotFoundError
            If enrollment not found
        """
        # Check if enrollment exists
        enrollment = crud_enrollment.get(db, obj_in.enrollment_id)
        if not enrollment:
            raise NotFoundError(detail="Enrollment not found")
        
        # Create payment
        return crud_payment.create(db, obj_in=obj_in)
    
    async def create_payment_intent(
        self, db: Session, *, payment_id: int, amount: float, currency: str = "usd"
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for a payment.
        
        Parameters
        ----------
        db: SQLAlchemy session
        payment_id: Payment ID
        amount: Payment amount
        currency: Payment currency (default: usd)
        
        Returns
        -------
        Dict[str, Any]
            Payment intent response with client secret
            
        Raises
        ------
        NotFoundError
            If payment not found
        ValidationError
            If Stripe operation fails
        """
        payment = crud_payment.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        try:
            # Convert amount to cents for Stripe (Stripe uses smallest currency unit)
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
            
            # Update payment with Stripe transaction ID for future reference
            crud_payment.update(
                db, 
                db_obj=payment, 
                obj_in={"transaction_id": intent.id}
            )
            
            return {
                "clientSecret": intent.client_secret,
                "payment_id": payment_id
            }
        except Exception as e:
            # Update payment status to failed if Stripe operation fails
            crud_payment.update_status(
                db, db_obj=payment, status=PaymentStatus.FAILED
            )
            raise ValidationError(detail=str(e))
    
    async def process_payment_webhook(
        self, db: Session, *, event_type: str, payment_intent: Dict[str, Any]
    ) -> Optional[Payment]:
        """
        Process a Stripe webhook event.
        
        Parameters
        ----------
        db: SQLAlchemy session
        event_type: Webhook event type
        payment_intent: Payment intent data from webhook
        
        Returns
        -------
        Optional[Payment]
            Updated payment if successful, None otherwise
        """
        # Only process successful payment events
        if event_type != "payment_intent.succeeded":
            return None
        
        transaction_id = payment_intent.get("id")
        if not transaction_id:
            return None
        
        # Find payment record by Stripe transaction ID
        payment = crud_payment.get_by_transaction_id(db, transaction_id=transaction_id)
        if not payment:
            return None
        
        # Update payment status to completed
        payment = crud_payment.update_status(
            db, db_obj=payment, status=PaymentStatus.COMPLETED
        )
        
        # Update enrollment payment status to reflect completed payment
        enrollment = crud_enrollment.get(db, id=payment.enrollment_id)
        if enrollment:
            crud_enrollment.update_payment_status(
                db, db_obj=enrollment, payment_status=PaymentStatus.PAID
            )
        
        return payment
    
    async def refund_payment(self, db: Session, *, payment_id: int) -> Payment:
        """
        Refund a payment via Stripe.
        
        Parameters
        ----------
        db: SQLAlchemy session
        payment_id: Payment ID to refund
        
        Returns
        -------
        Payment
            Updated payment instance
            
        Raises
        ------
        NotFoundError
            If payment not found
        ValidationError
            If refund conditions not met or Stripe operation fails
        """
        payment = crud_payment.get(db, payment_id)
        if not payment:
            raise NotFoundError(detail="Payment not found")
        
        if payment.status != PaymentStatus.COMPLETED:
            raise ValidationError(detail="Only completed payments can be refunded")
        
        if not payment.transaction_id:
            raise ValidationError(detail="Payment has no transaction ID")
        
        try:
            # Create Stripe refund for the payment intent
            refund = await stripe.Refund.create(
                payment_intent=payment.transaction_id
            )
            
            # Update payment status to refunded
            payment = crud_payment.update_status(
                db, db_obj=payment, status=PaymentStatus.REFUNDED
            )
            
            # Update enrollment payment status to reflect refund
            enrollment = crud_enrollment.get(db, id=payment.enrollment_id)
            if enrollment:
                crud_enrollment.update_payment_status(
                    db, db_obj=enrollment, payment_status=PaymentStatus.REFUNDED
                )
            
            return payment
        except Exception as e:
            raise ValidationError(detail=f"Refund failed: {str(e)}")
    
    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get payment statistics.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        Dict[str, Any]
            Payment statistics and financial metrics
        """
        return crud_payment.get_payment_stats(db)