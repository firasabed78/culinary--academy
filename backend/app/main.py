"""
main.py - FastAPI application entry point
This file initializes and configures the FastAPI application, including
middleware setup, routing, exception handling, startup events, and API
documentation. It serves as the main entry point for the backend service,
bringing together all components of the application.
"""

import logging  # Import logging module for application logging
from fastapi import FastAPI, Request, status  # Import FastAPI core components
from fastapi.middleware.cors import CORSMiddleware  # Import CORS middleware
from fastapi.responses import JSONResponse  # Import JSON response helper
from fastapi.openapi.docs import get_swagger_ui_html  # Import Swagger UI generator
from fastapi.staticfiles import StaticFiles  # Import static file handler
import os  # Import OS module for file system operations
from app.api.api_v1.api import api_router  # Import API router with all endpoints
from app.core.config import settings  # Import application settings
from app.db.init_db import init_db  # Import database initialization function

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define log format with timestamp and level
)
logger = logging.getLogger(__name__)  # Create logger for this module

# Initialize FastAPI application with metadata
app = FastAPI(
    title=settings.PROJECT_NAME,  # Application name from settings
    openapi_url=f"{settings.API_V1_STR}/openapi.json",  # Path to OpenAPI schema
    docs_url=None,  # Disable default Swagger UI to use custom implementation
)

# Set up Cross-Origin Resource Sharing (CORS) middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],  # List of allowed origins
        allow_credentials=True,  # Allow cookies in cross-origin requests
        allow_methods=["*"],  # Allow all HTTP methods
        allow_headers=["*"],  # Allow all HTTP headers
    )

# Create and mount uploads directory for file storage
uploads_dir = os.path.join(os.getcwd(), settings.UPLOAD_DIR)  # Get full path to uploads directory
os.makedirs(uploads_dir, exist_ok=True)  # Create directory if it doesn't exist
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")  # Mount directory to /uploads path

# Register API router with versioned prefix
app.include_router(api_router, prefix=settings.API_V1_STR)  # Include all API routes under /api/v1

# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to catch and log unhandled exceptions.
    Provides a generic error response to clients while logging detailed error information.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)  # Log exception with full stack trace
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,  # Return 500 status code
        content={"detail": "An unexpected error occurred. Please try again later."},  # Generic error message
    )

# Application startup event handler
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler triggered when the application starts.
    Initializes the database and performs other startup tasks.
    """
    logger.info("Starting up application")  # Log startup event
    init_db()  # Initialize database (create tables, seed data if needed)

# Root endpoint for basic API health check
@app.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint returning basic API information.
    Useful for health checks and API verification.
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}  # Welcome message with project name

# Custom Swagger UI endpoint
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    """
    Custom Swagger UI endpoint for API documentation.
    Uses CDN-hosted Swagger UI resources instead of the default FastAPI implementation.
    """
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",  # Path to OpenAPI schema
        title=f"{settings.PROJECT_NAME} - API Documentation",  # Documentation page title
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",  # Swagger UI JavaScript
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",  # Swagger UI CSS
    )