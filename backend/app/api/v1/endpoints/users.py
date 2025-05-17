"""
Objective: Implement course management endpoints.
This file defines the API endpoints for creating, retrieving, updating,
and deleting courses, with appropriate access control and filtering options.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api import deps
from app.domain.models.user import User
from app.domain.schemas.course import (
    Course, CourseCreate, CourseUpdate, CourseWithDetails
)
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService
from app.core.exceptions import NotFoundError, ValidationError

# Create a router for course endpoints
router = APIRouter()

# Create service instances
course_service = CourseService()
enrollment_service = EnrollmentService()

@router.get("/", response_model=List[Course])
def read_courses(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    instructor_id: Optional[int] = None,  # Filter by instructor
    is_active: Optional[bool] = None,  # Filter by active status
    category: Optional[str] = None,  # Filter by category
    search: Optional[str] = None,  # Search by title/description
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Retrieve courses with filtering.
    
    This endpoint returns a list of courses with optional filtering by instructor,
    active status, category, and search term.
    """
    # Build filters
    filters = {}
    if instructor_id:
        filters["instructor_id"] = instructor_id
    if is_active is not None:
        filters["is_active"] = is_active
    if category:
        filters["category"] = category
    if search:
        filters["search"] = search
    
    # For instructors, only show their own courses if no specific instructor is requested
    if current_user.role == "instructor" and not instructor_id:
        filters["instructor_id"] = current_user.id
    
    return course_service.get_filtered_courses(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=Course)
async def create_course(
    *,
    db: Session = Depends(deps.get_db),
    course_in: CourseCreate,  # Course data
    image: Optional[UploadFile] = File(None),  # Optional course image
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Create new course.
    
    This endpoint creates a new course with optional image upload.
    Only instructors can create courses assigned to themselves,
    while admins can create courses for any instructor.
    """
    try:
        # Check if user trying to create course for another instructor
        if current_user.role == "instructor" and course_in.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Instructors can only create courses for themselves"
            )
        
        # Create course with optional image
        return await course_service.create_course(
            db, 
            obj_in=course_in,
            image=image
        )
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=CourseWithDetails)
def read_course(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Course ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get course by ID with details.
    
    This endpoint returns a single course with detailed information,
    including schedules, instructor details, and enrollment counts.
    """
    try:
        # Get course with full details
        course = course_service.get_with_details(db, id)
        
        # Check if course is active or user has special access
        if not course.is_active and current_user.role == "student":
            # Students can only see active courses unless enrolled
            is_enrolled = enrollment_service.is_student_enrolled(
                db, student_id=current_user.id, course_id=course.id
            )
            if not is_enrolled:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Course not found or inactive"
                )
        
        return course
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}", response_model=Course)
async def update_course(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Course ID
    course_in: CourseUpdate,  # Update data
    image: Optional[UploadFile] = File(None),  # Optional new image
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Update course.
    
    This endpoint updates an existing course with optional image update.
    Instructors can only update their own courses, while admins can update any course.
    """
    try:
        # Get course
        course = course_service.get(db, id)
        
        # Check permissions
        if current_user.role == "instructor" and course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this course"
            )
        
        # Instructors cannot change course instructor
        if current_user.role == "instructor" and course_in.instructor_id and course_in.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Instructors cannot reassign courses to other instructors"
            )
        
        # Update course with optional image
        return await course_service.update_course(
            db, 
            id=id, 
            obj_in=course_in,
            image=image
        )
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{id}", response_model=Course)
def delete_course(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Course ID
    current_user: User = Depends(deps.get_current_admin),  # Admin user only
) -> Any:
    """
    Delete course.
    
    This endpoint marks a course as deleted.
    Only administrators can delete courses.
    """
    try:
        # Check if course has active enrollments
        active_enrollments = enrollment_service.count_active_enrollments(db, course_id=id)
        if active_enrollments > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete course with {active_enrollments} active enrollments"
            )
        
        # Delete course (soft delete)
        return course_service.soft_delete(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/instructor/{instructor_id}", response_model=List[Course])
def read_instructor_courses(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,  # Instructor ID
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    is_active: Optional[bool] = None,  # Filter by active status
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get courses taught by an instructor.
    
    This endpoint returns all courses taught by a specific instructor,
    with optional filtering by active status.
    """
    # Check permissions - instructors can only view their own courses
    if current_user.role == "instructor" and current_user.id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access another instructor's courses"
        )
    
    # Build filters
    filters = {"instructor_id": instructor_id}
    if is_active is not None:
        filters["is_active"] = is_active
    
    return course_service.get_filtered_courses(
        db, skip=skip, limit=limit, **filters
    )

@router.get("/{id}/students", response_model=List[dict])
def read_course_students(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Course ID
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Get students enrolled in a course.
    
    This endpoint returns all students enrolled in a specific course.
    Instructors can only view students in their own courses.
    """
    try:
        # Get course
        course = course_service.get(db, id)
        
        # Check permissions
        if current_user.role == "instructor" and course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this course's students"
            )
        
        # Get enrolled students
        return course_service.get_enrolled_students(db, course_id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )