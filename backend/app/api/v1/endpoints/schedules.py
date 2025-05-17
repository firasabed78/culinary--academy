from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import date, time

from app.api import deps
from app.domain.models.user import User
from app.domain.schemas.schedule import (
    Schedule, ScheduleCreate, ScheduleUpdate, ScheduleWithCourse
)
from app.services.schedule_service import ScheduleService
from app.services.course_service import CourseService
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
schedule_service = ScheduleService()
course_service = CourseService()

@router.get("/", response_model=List[Schedule])
def read_schedules(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    course_id: Optional[int] = None,
    day_of_week: Optional[int] = Query(None, ge=0, le=6),
    is_active: Optional[bool] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve schedules with filtering.
    """
    # Build filters
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
    schedule_in: ScheduleCreate,
    current_user: User = Depends(deps.get_current_instructor_or_admin),
) -> Any:
    """
    Create new schedule.
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=ScheduleWithCourse)
def read_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get schedule by ID with course details.
    """
    try:
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions for instructors
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this schedule"
            )
        
        return schedule
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.put("/{id}", response_model=Schedule)
def update_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    schedule_in: ScheduleUpdate,
    current_user: User = Depends(deps.get_current_instructor_or_admin),
) -> Any:
    """
    Update schedule.
    """
    try:
        # Get schedule with course
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this schedule"
            )
        
        # Update schedule
        return schedule_service.update_schedule(db, id=id, obj_in=schedule_in)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{id}", response_model=Schedule)
def delete_schedule(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_instructor_or_admin),
) -> Any:
    """
    Delete schedule.
    """
    try:
        # Get schedule with course
        schedule = schedule_service.get_with_course(db, id)
        
        # Check permissions
        if current_user.role == "instructor" and schedule.course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this schedule"
            )
        
        # Delete schedule
        return schedule_service.remove(db, id=id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/instructor/{instructor_id}", response_model=List[ScheduleWithCourse])
def read_instructor_schedules(
    *,
    db: Session = Depends(deps.get_db),
    instructor_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get schedules for courses taught by an instructor.
    """
    # Check permissions for instructor's own schedules
    if current_user.role == "instructor" and current_user.id != instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access another instructor's schedules"
        )
    
    return schedule_service.get_instructor_schedules(
        db, instructor_id=instructor_id, skip=skip, limit=limit
    )

@router.get("/course/{course_id}", response_model=List[Schedule])
def read_course_schedules(
    *,
    db: Session = Depends(deps.get_db),
    course_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all schedules for a course.
    """
    # Check if course exists
    course = course_service.get(db, course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    
    # Check permissions for instructors
    if current_user.role == "instructor" and course.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this course's schedules"
        )
    
    return schedule_service.get_course_schedules(db, course_id=course_id)