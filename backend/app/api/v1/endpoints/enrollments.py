from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.domain.models.user import User
from app.domain.models.enrollment import EnrollmentStatus, PaymentStatus
from app.domain.schemas.enrollment import (
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentWithDetails
)
from app.services.enrollment_service import EnrollmentService
from app.services.notification_service import NotificationService
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
enrollment_service = EnrollmentService()
notification_service = NotificationService()

@router.get("/", response_model=List[Enrollment])
def read_enrollments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    status: Optional[EnrollmentStatus] = None,
    payment_status: Optional[PaymentStatus] = None,
    student_id: Optional[int] = None,
    course_id: Optional[int] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve enrollments with filtering.
    """
    # Build filters
    filters = {}
    if status:
        filters["status"] = status
    if payment_status:
        filters["payment_status"] = payment_status
    
    # Apply access control based on user role
    if current_user.role == "student":
        # Students can only see their own enrollments
        filters["student_id"] = current_user.id
    elif current_user.role == "instructor":
        # If student_id is specified, verify it's for a student in instructor's course
        if student_id:
            filters["student_id"] = student_id
        
        # Instructors can only see enrollments for their courses
        if course_id:
            filters["course_id"] = course_id
        else:
            # Get all courses taught by this instructor
            instructor_courses = course_service.get_instructor_courses(db, instructor_id=current_user.id)
            if not instructor_courses:
                return []
            filters["course_id"] = [course.id for course in instructor_courses]
    else:
        # Admins can see all enrollments with optional filters
        if student_id:
            filters["student_id"] = student_id
        if course_id:
            filters["course_id"] = course_id
    
    return enrollment_service.get_filtered_enrollments(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=Enrollment)
def create_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    enrollment_in: EnrollmentCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new enrollment.
    """
    # Only allow students to enroll themselves or admins to enroll anyone
    if current_user.role == "student" and enrollment_in.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only enroll themselves"
        )
    
    try:
        enrollment = enrollment_service.create_enrollment(db, obj_in=enrollment_in)
        
        # Create notification for student
        notification_service.create_system_notification(
            db,
            user_id=enrollment.student_id,
            title="Enrollment Submitted",
            message=f"Your enrollment for {enrollment.course.title} has been submitted and is pending approval.",
            entity_id=enrollment.id,
            entity_type="enrollment",
            send_email=True
        )
        
        # If course has instructor, notify them too
        if enrollment.course.instructor_id:
            notification_service.create_system_notification(
                db,
                user_id=enrollment.course.instructor_id,
                title="New Enrollment",
                message=f"A new student has enrolled in your course {enrollment.course.title}.",
                entity_id=enrollment.id,
                entity_type="enrollment"
            )
        
        return enrollment
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=EnrollmentWithDetails)
def read_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get enrollment by ID with all related details.
    """
    try:
        enrollment = enrollment_service.get_with_relations(db, id)
        
        # Check permissions
        if current_user.role == "student" and enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this enrollment"
            )
        elif current_user.role == "instructor" and enrollment.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this enrollment"
            )
        
        return enrollment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}", response_model=Enrollment)
def update_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    enrollment_in: EnrollmentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update enrollment.
    """
    try:
        enrollment = enrollment_service.get(db, id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        
        # Check permissions
        if current_user.role == "student" and enrollment.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this enrollment"
            )
        elif current_user.role == "instructor" and enrollment.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this enrollment"
            )
        
        # Students can only update notes
        if current_user.role == "student":
            if enrollment_in.status or enrollment_in.payment_status:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Students can only update notes"
                )
        
        # Instructors can update status but not payment_status
        if current_user.role == "instructor" and enrollment_in.payment_status:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Instructors cannot update payment status"
            )
        
        # Update enrollment
        updated_enrollment = enrollment_service.update(db, id=id, obj_in=enrollment_in)
        
        # If status changed, create notification
        if enrollment_in.status and enrollment_in.status != enrollment.status:
            notification_service.create_system_notification(
                db,
                user_id=enrollment.student_id,
                title=f"Enrollment {enrollment_in.status.value.capitalize()}",
                message=f"Your enrollment for {enrollment.course.title} has been {enrollment_in.status.value}.",
                entity_id=enrollment.id,
                entity_type="enrollment",
                send_email=True
            )
        
        return updated_enrollment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/stats", response_model=dict)
def get_enrollment_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),
) -> Any:
    """
    Get enrollment statistics (admin only).
    """
    return enrollment_service.get_enrollment_stats(db)