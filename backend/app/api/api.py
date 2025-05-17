"""
Objective: Define the main API router for the application.
This file serves as the API entry point, organizing different API versions
and providing a structured routing hierarchy for all API endpoints.

This simple but important file sets up the API versioning structure:

Purpose: Creates the main entry point for all API endpoints and establishes API versioning.
Key Features:

Implements API versioning with the /v1 prefix
Creates a modular structure that would allow for future API versions (v2, v3, etc.)
Centralizes the routing logic for the entire API


Design Pattern:

Uses a hierarchical router structure (main router → version router → feature routers)
Follows API best practices by including explicit versioning in the URL paths


Integration Points:

Links to the v1 router, which would contain the feature-specific endpoints
Would be included in the main FastAPI application to mount all API routes



This structure allows the application to maintain backward compatibility when introducing breaking changes by implementing new API versions while keeping existing ones functional.

"""

from fastapi import APIRouter  # Import FastAPI's router for endpoint organization
from app.api.v1.router import api_router as api_v1_router  # Import the v1 API router

# Create the main API router that will include all versions
api_router = APIRouter()

# Include the v1 API router with a prefix to create the versioned API path structure
# All v1 endpoints will be accessible under the "/v1" URL prefix
api_router.include_router(api_v1_router, prefix="/v1")