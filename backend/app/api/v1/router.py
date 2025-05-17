"""
Objective: Configure and organize the API routes.
This file registers all API endpoint routers under the main API router,
organizing them by feature area with appropriate URL prefixes and tags.

This file organizes all API routes for version 1 of the API:

Purpose: Centralizes and organizes all API endpoints into a structured hierarchy with logical grouping.
Key Features:

Domain-Based Organization: Routes are grouped by domain/feature (auth, users, courses, etc.)
URL Hierarchy: Each domain has its own URL prefix (e.g., /auth, /users, /courses)
Swagger/OpenAPI Integration: Uses tags for API documentation grouping
Modular Structure: Each feature has its own router in a separate file


Design Pattern:

Hierarchical Router Structure: Main router → Domain router → Individual endpoints
Separation of Concerns: Each feature area has its own dedicated router
API Versioning: Part of the v1 API (supports future versions if needed)


URL Structure:

All routes will be under /api/v1/{domain}/{endpoint}
For example:

Authentication: /api/v1/auth/login
Users: /api/v1/users/{id}
Courses: /api/v1/courses/{id}




Benefits:

Organized Documentation: The tag system provides clear API documentation grouping in Swagger UI
Maintainability: Easy to add, remove, or update feature-specific endpoints
Discoverability: Logical URL structure makes API endpoints easy to find and use
Scalability: Structure supports growing the API with new features



This router setup follows RESTful API best practices by organizing resources into logical groups with consistent URL patterns, making the API intuitive for consumers and maintainable for developers.
"""

from fastapi import APIRouter  # Import FastAPI's router for organizing endpoints
from app.api.v1.endpoints import auth, users, courses, enrollments, payments, schedules, documents, notifications

# Create the main v1 API router
api_router = APIRouter()

# Register feature-specific routers with appropriate prefixes and tags

# Authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",  # All auth endpoints will be under /api/v1/auth/*
    tags=["authentication"]  # Swagger/OpenAPI tag for grouping
)

# User management endpoints
api_router.include_router(
    users.router,
    prefix="/users",  # All user endpoints will be under /api/v1/users/*
    tags=["users"]  # Swagger/OpenAPI tag for grouping
)

# Course management endpoints
api_router.include_router(
    courses.router,
    prefix="/courses",  # All course endpoints will be under /api/v1/courses/*
    tags=["courses"]  # Swagger/OpenAPI tag for grouping
)

# Enrollment management endpoints
api_router.include_router(
    enrollments.router,
    prefix="/enrollments",  # All enrollment endpoints will be under /api/v1/enrollments/*
    tags=["enrollments"]  # Swagger/OpenAPI tag for grouping
)

# Payment management endpoints
api_router.include_router(
    payments.router,
    prefix="/payments",  # All payment endpoints will be under /api/v1/payments/*
    tags=["payments"]  # Swagger/OpenAPI tag for grouping
)

# Schedule management endpoints
api_router.include_router(
    schedules.router,
    prefix="/schedules",  # All schedule endpoints will be under /api/v1/schedules/*
    tags=["schedules"]  # Swagger/OpenAPI tag for grouping
)

# Document management endpoints
api_router.include_router(
    documents.router,
    prefix="/documents",  # All document endpoints will be under /api/v1/documents/*
    tags=["documents"]  # Swagger/OpenAPI tag for grouping
)

# Notification management endpoints
api_router.include_router(
    notifications.router,
    prefix="/notifications",  # All notification endpoints will be under /api/v1/notifications/*
    tags=["notifications"]  # Swagger/OpenAPI tag for grouping
)