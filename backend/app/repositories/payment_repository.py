"""
Objective: Implement a specialized repository for payment operations.
This file extends the base repository with payment-specific query methods,
providing functionality for tracking, aggregating, and reporting on payments.


The PaymentRepository focuses on the financial aspects of your application, providing specialized methods for tracking and analyzing payment transactions.
Key Features:

Payment Tracking Operations:

Transaction Reference: Finding payments by external transaction IDs
Enrollment Association: Retrieving all payments for a specific enrollment
Status Management: Tracking and updating payment status
Date Filtering: Finding payments within specific date ranges


Financial Aggregation:

Total Calculations: Computing the total amount of payments
Period-Based Totals: Calculating payment totals within date ranges
Status-Based Totals: Filtering totals by payment status (e.g., completed only)
Statistics Gathering: Collecting comprehensive payment metrics


Payment Analysis:

Status Distribution: Counting payments by various status types
Statistical Reports: Generating comprehensive payment statistics
Financial Reporting: Methods supporting financial dashboards


Technical Patterns:

Aggregate Queries: Using SQL aggregation functions
Type Handling: Proper conversion of SQL results to Python types
Date Range Filtering: Implementing time-based queries
Status-Based Filtering: Using enum values for type-safe filtering



This repository plays a crucial role in the financial management aspects of your culinary academy application. It supports important business functions like:

Revenue Tracking: Methods to calculate total completed payments
Financial Reporting: Date-range based calculations for reports
Payment Verification: Looking up payments by transaction ID for verification
Dashboard Analytics: Generating statistics for administrative dashboards
Enrollment Financials: Tracking payments associated with specific enrollments

The aggregation methods are particularly important for administrative and financial dashboards, allowing your application to present current financial status and trends without complex calculations at the UI level.
This repository demonstrates SQL aggregation techniques through SQLAlchemy, properly handling NULL results and type conversions to ensure reliable financial calculations.

"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships
from datetime import datetime

from app.domain.models.payment import Payment, PaymentStatus
from app.domain.schemas.payment import PaymentCreate, PaymentUpdate
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment, PaymentCreate, PaymentUpdate]):
    """
    Repository for payment operations.
    
    Extends the base repository with payment-specific queries for
    retrieving, filtering, and analyzing payment transactions.
    """
    
    def __init__(self):
        """Initialize with Payment model."""
        super().__init__(Payment)

    def get_with_relations(self, db: Session, id: int) -> Optional[Payment]:
        """
        Get a payment with related enrollment data.
        
        Uses eager loading to retrieve a payment with its associated enrollment
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Payment ID
            
        Returns:
            Payment with loaded enrollment relationship or None if not found
        """
        return db.query(self.model)\
            .options(joinedload(self.model.enrollment))\
            .filter(self.model.id == id)\
            .first()

    def get_by_transaction_id(self, db: Session, *, transaction_id: str) -> Optional[Payment]:
        """
        Get payment by transaction ID.
        
        Retrieves a payment by its external transaction ID, typically from
        a payment gateway like Stripe.
        
        Args:
            db: SQLAlchemy database session
            transaction_id: External payment gateway transaction ID
            
        Returns:
            Matching payment or None if not found
        """
        return db.query(self.model)\
            .filter(self.model.transaction_id == transaction_id)\
            .first()

    def get_by_enrollment(self, db: Session, *, enrollment_id: int) -> List[Payment]:
        """
        Get all payments for an enrollment.
        
        Retrieves all payment transactions associated with a specific enrollment.
        
        Args:
            db: SQLAlchemy database session
            enrollment_id: Enrollment ID
            
        Returns:
            List of payments for the specified enrollment
        """
        return db.query(self.model)\
            .filter(self.model.enrollment_id == enrollment_id)\
            .all()

    def get_by_status(
        self, db: Session, *, status: PaymentStatus, skip: int = 0, limit: int = 100
    ) -> List[Payment]:
        """
        Get payments by status.
        
        Retrieves payments with a specific status (e.g., completed, pending, failed)
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            status: PaymentStatus enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of payments with the specified status
        """
        return db.query(self.model)\
            .filter(self.model.status == status)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def update_status(
        self, db: Session, *, db_obj: Payment, status: PaymentStatus
    ) -> Payment:
        """
        Update payment status.
        
        Updates a payment's status (e.g., from pending to completed)
        and persists the change to the database.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Payment object to update
            status: New payment status
            
        Returns:
            Updated payment object
        """
        db_obj.status = status  # Set new status
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get updated values
        return db_obj

    def get_payments_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime
    ) -> List[Payment]:
        """
        Get payments within a date range.
        
        Retrieves all payments that occurred between the specified dates.
        
        Args:
            db: SQLAlchemy database session
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of payments within the date range
        """
        return db.query(self.model)\
            .filter(
                self.model.payment_date >= start_date,
                self.model.payment_date <= end_date
            )\
            .all()

    def get_total_amount(self, db: Session) -> float:
        """
        Get total amount of all completed payments.
        
        Calculates the sum of all completed payment amounts.
        
        Args:
            db: SQLAlchemy database session
            
        Returns:
            Total amount of completed payments
        """
        # Use SQLAlchemy's aggregation functions
        result = db.query(
            db.func.sum(self.model.amount)
        ).filter(
            self.model.status == PaymentStatus.COMPLETED
        ).scalar()
        
        return float(result) if result else 0.0  # Convert to float or default to 0

    def get_total_amount_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime
    ) -> float:
        """
        Get total amount of completed payments within a date range.
        
        Calculates the sum of completed payment amounts within the specified dates.
        
        Args:
            db: SQLAlchemy database session
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            Total amount of completed payments within the date range
        """
        # Use SQLAlchemy's aggregation functions with date range filtering
        result = db.query(
            db.func.sum(self.model.amount)
        ).filter(
            self.model.payment_date >= start_date,
            self.model.payment_date <= end_date,
            self.model.status == PaymentStatus.COMPLETED
        ).scalar()
        
        return float(result) if result else 0.0  # Convert to float or default to 0

    def get_payment_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get payment statistics.
        
        Aggregates statistics about payments, including counts by status
        and total amounts.
        
        Args:
            db: SQLAlchemy database session
            
        Returns:
            Dictionary of payment statistics
        """
        # Count all payments
        total_payments = db.query(self.model).count()
        
        # Get total amount of completed payments
        total_amount = self.get_total_amount(db)
        
        # Count payments by status
        completed_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.COMPLETED)\
            .count()
        
        pending_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.PENDING)\
            .count()
        
        failed_payments = db.query(self.model)\
            .filter(self.model.status == PaymentStatus.FAILED)\
            .count()
        
        # Return consolidated statistics
        return {
            "total": total_payments,
            "totalAmount": total_amount,
            "completed": completed_payments,
            "pending": pending_payments,
            "failed": failed_payments
        }