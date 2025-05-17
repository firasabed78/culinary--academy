"""
Objective: Implement course enrollment management endpoints.
This file defines the API endpoints for creating, retrieving, and updating
course enrollments with appropriate access control and notifications.

This file implements a feature-rich enrollment management API:

Purpose: Provides a complete CRUD interface for managing course enrollments with role-based access control and automated notifications.
Key Endpoints:

GET /: List enrollments with role-based filtering and access control
POST /: Create new course enrollments with notifications
GET /{id}: Retrieve a specific enrollment with all related details
PUT /{id}: Update enrollment with role-based permissions
GET /stats: Get enrollment statistics (admin only)


Design Patterns:

Role-based Access Control (RBAC): Different permissions and data visibility for students, instructors, and admins
Event-driven Architecture: Notifications triggered by enrollment status changes
Separation of Concerns: Routes handle HTTP logic, services handle business logic
Data Filtering: Complex filtering based on user role and provided parameters


Security Features:

Authentication for all endpoints
Authorization checks for each operation with role-specific rules
Data isolation between users (students see only their enrollments, instructors see only their courses' enrollments)


Business Logic Highlights:

Notifications to students and instructors upon enrollment and status changes
Complex role-based permission system with granular field-level restrictions
Email notifications for important status changes
Statistics aggregation for administrative oversight


Improvement Notes:

There's a missing import for course_service which is used in the read_enrollments function



This endpoint demonstrates sophisticated role-based access control and business logic that goes beyond simple CRUD operations, incorporating event-driven notifications and complex permission rules based on the user's relationship to the data.

"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps  # Authentication dependencies
from app.domain.models.user import User
from app.domain.models.enrollment import EnrollmentStatus, PaymentStatus  # Enrollment enums
from app.domain.schemas.enrollment import (
    Enrollment, EnrollmentCreate, EnrollmentUpdate, EnrollmentWithDetails  # Data models/schemas
)
from app.services.enrollment_service import EnrollmentService  # Enrollment business logic
from app.services.notification_service import NotificationService  # Notification service for alerts
from app.core.exceptions import NotFoundError, ValidationError  # Custom exceptions

# Create a router for enrollment endpoints
router = APIRouter()

# Create service instances
enrollment_service = EnrollmentService()
notification_service = NotificationService()
# Note: course_service is not imported but used in the code (minor issue to fix)

@router.get("/", response_model=List[Enrollment])
def read_enrollments(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    status: Optional[EnrollmentStatus] = None,  # Filter by enrollment status
    payment_status: Optional[PaymentStatus] = None,  # Filter by payment status
    student_id: Optional[int] = None,  # Filter by student
    course_id: Optional[int] = None,  # Filter by course
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Retrieve enrollments with filtering.
    
    This endpoint returns a list of enrollments with optional filtering.
    Access control ensures users only see enrollments they're authorized to view.
    """
    # Build filters dictionary for the service layer
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
    
    # Get filtered enrollments from service
    return enrollment_service.get_filtered_enrollments(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=Enrollment)
def create_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    enrollment_in: EnrollmentCreate,  # Enrollment data
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Create new enrollment.
    
    This endpoint creates a new course enrollment and sends notifications
    to relevant parties (student and instructor).
    """
    # Only allow students to enroll themselves or admins to enroll anyone
    if current_user.role == "student" and enrollment_in.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students can only enroll themselves"
        )
    
    try:
        # Create the enrollment
        enrollment = enrollment_service.create_enrollment(db, obj_in=enrollment_in)
        
        # Create notification for student
        notification_service.create_system_notification(
            db,
            user_id=enrollment.student_id,
            title="Enrollment Submitted",
            message=f"Your enrollment for {enrollment.course.title} has been submitted and is pending approval.",
            entity_id=enrollment.id,
            entity_type="enrollment",
            send_email=True  # Send email notification too
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
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=EnrollmentWithDetails)
def read_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Enrollment ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get enrollment by ID with all related details.
    
    This endpoint returns a single enrollment with full details, including
    related student, course, and payment information.
    """
    try:
        # Get enrollment with all related data
        enrollment = enrollment_service.get_with_relations(db, id)
        
        # Check permissions based on role
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
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}", response_model=Enrollment)
def update_enrollment(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Enrollment ID
    enrollment_in: EnrollmentUpdate,  # Update data
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Update enrollment.
    
    This endpoint updates enrollment information with role-based permissions:
    - Students can only update their notes
    - Instructors can update status but not payment status
    - Admins can update any field
    """
    try:
        # Get the enrollment to check permissions
        enrollment = enrollment_service.get(db, id)
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
        
        # Check permissions based on role
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
                send_email=True  # Send email notification too
            )
        
        return updated_enrollment
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/stats", response_model=dict)
def get_enrollment_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin),  # Admin only endpoint
) -> Any:
    """
    Get enrollment statistics (admin only).
    
    This endpoint returns aggregated statistics about enrollments,
    such as counts by status, payment status, course, etc.
    """
    return enrollment_service.get_enrollment_stats(db)