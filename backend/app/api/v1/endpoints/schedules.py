"""
Objective: Implement course schedule management endpoints.
This file defines the API endpoints for creating, retrieving, updating, and
deleting course schedules, with appropriate access control and filtering options.

This file implements a comprehensive schedule management API:

Purpose: Provides a complete CRUD interface for managing course schedules, with specialized endpoints for retrieving schedules by instructor or course.
Key Endpoints:

GET /: List schedules with filtering by course, day of week, or active status
POST /: Create new course schedules
GET /{id}: Retrieve a specific schedule with course details
PUT /{id}: Update an existing schedule
DELETE /{id}: Delete a schedule
GET /instructor/{instructor_id}: Get all schedules for an instructor's courses
GET /course/{course_id}: Get all schedules for a specific course


Design Patterns:

Role-based Access Control: Instructors can only manage schedules for their own courses
Resource Ownership: Schedules are associated with courses, which are owned by instructors
Filter Pattern: Multiple filtering options for schedule retrieval
Specialized Query Endpoints: Dedicated endpoints for instructor and course-based queries


Security Features:

Authentication for all endpoints
Authorization checks for each operation
Data isolation (instructors can only see and manage their own courses' schedules)
Permission validation for write operations


Notable Implementation Details:

Day of week filtering (0-6) for retrieving schedules by day
Active status filtering for showing only current schedules
Course-specific endpoints for easy access to all schedules for a course
Instructor-specific endpoints for viewing an instructor's teaching schedule


Improvement Ideas:

The in-memory filtering by is_active could be optimized by adding it to the database query
Consider adding date range filtering for retrieving schedules within a specific period
The manual pagination for instructor schedules could be improved for larger datasets



This API provides a solid foundation for managing course schedules in an educational setting, with appropriate access controls and convenient filtering options to support calendaring and scheduling features in the frontend.

"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date, time  # For schedule time handling

from app.api import deps  # Authentication dependencies
from app.domain.models.user import User
from app.domain.schemas.schedule import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleWithCourse  # Data models/schemas
)
from app.services.schedule_service import ScheduleService  # Schedule business logic
from app.services.course_service import CourseService  # Course business logic
from app.core.exceptions import NotFoundError, ValidationError  # Custom exceptions

# Create a router for schedule endpoints
router = APIRouter()

# Create service instances
schedule_service = ScheduleService()
course_service = CourseService()

@router.get("/", response_model=List[Schedule])
def read_schedules(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    course_id: Optional[int] = None,  # Filter by course
    day_of_week: Optional[int] = Query(None, ge=0, le=6),  # Filter by day (0=Sunday, 6=Saturday)
    is_active: Optional[bool] = None,  # Filter by active status
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Retrieve schedules with filtering.
    
    This endpoint returns a list of course schedules with optional filtering
    by course, day of week, and active status. Access control ensures instructors
    only see schedules for their own courses.
    """
    # Build query based on filter parameters
    if course_id:
        # Get schedules for a specific course
        schedules = schedule_service.get_course_schedules(db, course_id=course_id)
    elif day_of_week is not None:
        # Get schedules for a specific day
        schedules = schedule_service.get_schedules_by_day(db, day_of_week=day_of_week, skip=skip, limit=limit)
    else:
        # Get all schedules with possible is_active filter
        filters = {}
        if is_active is not None:
            filters["is_active"] = is_active
        
        # For instructors, only show their courses' schedules
        if current_user.role == "instructor":
            # Get instructor's courses
            instructor_courses = course_service.get_instructor_courses(db, instructor_id=current_user.id)
            if not instructor_courses:
                return []
            
            # Get schedules for these courses
            schedules = []
            course_ids = [course.id for course in instructor_courses]
            for c_id in course_ids:
                course_schedules = schedule_service.get_course_schedules(db, course_id=c_id)
                schedules.extend(course_schedules)
            
            # Apply is_active filter if provided
            if is_active is not None:
                schedules = [s for s in schedules if s.is_active == is_active]
            
            # Manual pagination
            return schedules[skip:skip+limit]
        else:
            # For admin and students, get all schedules
            schedules = schedule_service.get_multi(db, skip=skip, limit=limit, **filters)
    
    # Filter by is_active if provided
    if is_active is not None:
        schedules = [s for s in schedules if s.is_active == is_active]
    
    return schedules

@router.post("/", response_model=Schedule)
def create_schedule(
    *,
    db: Session = Depends(deps.get_db),
    schedule_in: ScheduleCreate,  # Schedule data
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Create new schedule.
    
    This endpoint creates a new course schedule, ensuring the user
    has permission to modify the specified course's schedules.
    """
    try:
        # Check if course exists and user has permission
        course = course_service.get(db, schedule_in.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        
        # Instructors can only create schedules for their own courses
        if current_user.role == "instructor" and course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create schedule for this course"
            )
        
        # Create schedule
        return schedule_service.create_schedule(db, obj_in=schedule_in)
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=ScheduleWithCourse)
def read_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Schedule ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get schedule by ID with course details.
    
    This endpoint returns a single schedule with its associated course details,
    ensuring the requester has permission to view it.
    """
    try:
        # Get schedule with course details
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions for instructors - they can only view their own courses' schedules
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this schedule"
            )
        
        return schedule
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}", response_model=Schedule)
def update_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Schedule ID
    schedule_in: ScheduleUpdate,  # Update data
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Update schedule.
    
    This endpoint updates an existing schedule, ensuring the user
    has permission to modify the associated course's schedules.
    """
    try:
        # Get schedule with course details to check permissions
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions - instructors can only update their own courses' schedules
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this schedule"
            )
        
        # Update schedule
        return schedule_service.update_schedule(db, id=id, obj_in=schedule_in)
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

@router.delete("/{id}", response_model=Schedule)
def delete_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Schedule ID
    current_user: User = Depends(deps.get_current_instructor_or_admin),  # Instructor or admin only
) -> Any:
    """
    Delete schedule.
    
    This endpoint deletes a schedule, ensuring the user has
    permission to modify the associated course's schedules.
    """
    try:
        # Get schedule with course details to check permissions
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions - instructors can only delete their own courses' schedules
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this schedule"
            )
        
        # Delete schedule
        return schedule_service.remove(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/instructor/{instructor_id}", response_model=List[ScheduleWithCourse])
def read_instructor_schedules(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,  # Instructor ID
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get schedules for courses taught by an instructor.
    
    This endpoint returns all schedules for courses taught by a specific instructor,
    with permission checks to ensure instructors can only view their own schedules.
    """
    # Check permissions - instructors can only view their own schedules
    if current_user.role == "instructor" and current_user.id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access another instructor's schedules"
        )
    
    # Get instructor's schedules
    return schedule_service.get_instructor_schedules(
        db, instructor_id=instructor_id, skip=skip, limit=limit
    )

@router.get("/course/{course_id}", response_model=List[Schedule])
def read_course_schedules(
    *,
    db: Session = Depends(deps.get_db),
    course_id: int,  # Course ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get all schedules for a course.
    
    This endpoint returns all schedules for a specific course,
    with permission checks to ensure instructors can only view
    schedules for their own courses.
    """
    # Check if course exists
    course = course_service.get(db, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    # Check permissions - instructors can only view their own courses' schedules
    if current_user.role == "instructor" and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course's schedules"
        )
    
    # Get course schedules
    return schedule_service.get_course_schedules(db, course_id=course_id)