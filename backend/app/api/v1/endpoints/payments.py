from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.domain.models.user import User
from app.domain.models.payment import PaymentStatus, PaymentMethod
from app.domain.schemas.payment import (
    Payment, PaymentCreate, PaymentUpdate, PaymentWithEnrollment
)
from app.services.payment_service import PaymentService
from app.services.enrollment_service import EnrollmentService
from app.services.notification_service import NotificationService
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
payment_service = PaymentService()
enrollment_service = EnrollmentService()
notification_service = NotificationService()

@router.get("/", response_model=List[Payment])
def read_payments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[PaymentStatus] = None,
    payment_method: Optional[PaymentMethod] = None,
    enrollment_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve payments with filtering.
    """
    # Build base query
    if enrollment_id:
        # First check if user has access to this enrollment
        try:
            enrollment = enrollment_service.get(db, enrollment_id)
            if not enrollment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
            
            # Check permissions
            if current_user.role == "student" and enrollment.student_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this enrollment's payments"
                )
            elif current_user.role == "instructor" and enrollment.course.instructor_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this enrollment's payments"
                )
            
            # Get payments for this enrollment
            payments = payment_service.repository.get_by_enrollment(db, enrollment_id=enrollment_id)
            
            # Apply filters
            if status:
                payments = [p for p in payments if p.status == status]
            if payment_method:
                payments = [p for p in payments if p.payment_method == payment_method]
            
            return payments
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
    
    # For admins, allow fetching all payments with filters
    if current_user.role == "admin":
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if payment_method:
            filters["payment_method"] = payment_method
        
        # Date range filtering (handled in service)
        if start_date and end_date:
            return payment_service.repository.get_payments_by_date_range(
                db, start_date=start_date, end_date=end_date
            )
        
        return payment_service.get_multi(db, skip=skip, limit=limit, **filters)
    
    # For students, get payments for their enrollments
    if current_user.role == "student":
        enrollments = enrollment_service.get_student_enrollments(db, student_id=current_user.id)
        if not enrollments:
            return []
        
        enrollment_ids = [e.id for e in enrollments]
        all_payments = []
        
        for e_id in enrollment_ids:
            payments = payment_service.repository.get_by_enrollment(db, enrollment_id=e_id)
            all_payments.extend(payments)
        
        # Apply filters
        if status:
            all_payments = [p for p in all_payments if p.status == status]
        if payment_method:
            all_payments = [p for p in all_payments if p.payment_method == payment_method]
        
        # Manual pagination (inefficient but works for small datasets)
        return all_payments[skip:skip+limit]
    
    # For instructors, get payments for their courses' enrollments
    if current_user.role == "instructor":
        # Get all courses taught by this instructor
        instructor_courses = course_service.get_instructor_courses(db, instructor_id=current_user.id)
        if not instructor_courses:
            return []
        
        course_ids = [course.id for course in instructor_courses]
        all_payments = []
        
        # Get enrollments for these courses
        for c_id in course_ids:
            enrollments = enrollment_service.get_course_enrollments(db, course_id=c_id)
            for enrollment in enrollments:
                payments = payment_service.repository.get_by_enrollment(db, enrollment_id=enrollment.id)
                all_payments.extend(payments)
        
        # Apply filters
        if status:
            all_payments = [p for p in all_payments if p.status == status]
        if payment_method:
            all_payments = [p for p in all_payments if p.payment_method == payment_method]
        
        # Manual pagination
        return all_payments[skip:skip+limit]

@router.post("/", response_model=Payment)
def create_payment(
    *,
    db: Session = Depends(deps.get_db),
    payment_in: PaymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new payment.
    """
    try:
        # Check if enrollment exists and user has permission
        enrollment = enrollment_service.get(db, payment_in.enrollment_id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        
        # Only students can pay for their own enrollments or admins can create payments
        if current_user.role == "student" and enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create payment for this enrollment"
            )
        
        # Create payment
        payment = payment_service.create_payment(db, obj_in=payment_in)
        
        # Create payment intent in background
        background_tasks.add_task(
            payment_service.create_payment_intent,
            db=db,
            payment_id=payment.id,
            amount=payment.amount,
            currency="usd"
        )
        
        return payment
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=PaymentWithEnrollment)
def read_payment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get payment by ID with enrollment details.
    """
    try:
        payment = payment_service.get_with_relations(db, id)
        
        # Check permissions
        if current_user.role == "student" and payment.enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this payment"
            )
        elif current_user.role == "instructor" and payment.enrollment.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this payment"
            )
        
        return payment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.post("/{id}/refund", response_model=Payment)
async def refund_payment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Refund a payment (admin only).
    """
    try:
        payment = await payment_service.refund_payment(db, payment_id=id)
        
        # Create notification for the student
        background_tasks.add_task(
            notification_service.create_system_notification,
            db=db,
            user_id=payment.enrollment.student_id,
            title="Payment Refunded",
            message=f"Your payment of ${payment.amount:.2f} for {payment.enrollment.course.title} has been refunded.",
            entity_id=payment.id,
            entity_type="payment",
            send_email=True
        )
        
        return payment
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/{id}/intent", response_model=dict)
async def create_payment_intent(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create a payment intent for an existing payment.
    """
    try:
        payment = payment_service.get_with_relations(db, id)
        
        # Check permissions
        if current_user.role == "student" and payment.enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create intent for this payment"
            )
        
        return await payment_service.create_payment_intent(
            db, payment_id=id, amount=payment.amount, currency="usd"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook_received(
    *,
    db: Session = Depends(deps.get_db),
    background_tasks: BackgroundTasks,
    payload: dict,
) -> Any:
    """
    Handle Stripe webhook events.
    """
    event_type = payload.get("type")
    event_data = payload.get("data", {}).get("object", {})
    
    try:
        payment = await payment_service.process_payment_webhook(
            db, event_type=event_type, payment_intent=event_data
        )
        
        if payment and payment.status == PaymentStatus.COMPLETED:
            # Notify student about successful payment
            background_tasks.add_task(
                notification_service.create_system_notification,
                db=db,
                user_id=payment.enrollment.student_id,
                title="Payment Successful",
                message=f"Your payment of ${payment.amount:.2f} for {payment.enrollment.course.title} has been processed successfully.",
                entity_id=payment.id,
                entity_type="payment",
                send_email=True
            )
        
        return {"status": "success"}
    except Exception as e:
        # Log error but return success to Stripe
        print(f"Error processing webhook: {str(e)}")
        return {"status": "success"}

@router.get("/stats", response_model=dict)
def get_payment_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Get payment statistics (admin only).
    """
    return payment_service.get_payment_stats(db)