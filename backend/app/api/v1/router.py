from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, courses, enrollments, payments, schedules, documents, notifications

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(courses.router, prefix="/courses", tags=["courses"])
api_router.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["schedules"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])