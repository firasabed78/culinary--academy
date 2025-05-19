"""
validation.py - Input validation utilities for API endpoints
This file provides reusable validation functions for common validation 
scenarios in FastAPI endpoint handlers, including data validation against
Pydantic models, existence checks, uniqueness validation, permission verification,
and file validation. These utilities help ensure data integrity and provide
consistent error responses across the API.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar  # Import typing utilities for type hints
from fastapi import HTTPException, status  # Import FastAPI exception handling and status codes
from pydantic import BaseModel, ValidationError  # Import Pydantic validation utilities

# Define generic type variable for Pydantic models
ModelType = TypeVar("ModelType", bound=BaseModel)  # Type variable restricted to Pydantic models

def validate_model(model_class: Type[ModelType], data: Dict[str, Any]) -> ModelType:
    """
    Validate data against a Pydantic model and return the validated model.
    Raises an HTTPException with appropriate status code on validation error.
    
    Args:
        model_class: Pydantic model class to validate against
        data: Dictionary containing data to validate
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        HTTPException: If validation fails, with 422 status code and detailed error messages
    """
    try:
        # Attempt to create and validate model instance
        return model_class(**data)
    except ValidationError as e:
        # Format validation errors for clear client feedback
        errors = []
        for error in e.errors():
            # Convert location path (e.g., ['address', 'city']) to dot notation (e.g., 'address.city')
            loc = ".".join(str(l) for l in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
        
        # Raise HTTP exception with formatted error details
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Validation error", "errors": errors}
        )

def validate_id_exists(item: Optional[Any], id: int, item_name: str) -> None:
    """
    Validate that an item with the specified ID exists.
    Raises an HTTPException with appropriate status code if not found.
    
    Args:
        item: The item fetched from database (None if not found)
        id: The ID that was searched for
        item_name: Human-readable name of the item type (e.g., "User", "Course")
        
    Raises:
        HTTPException: If item is None, with 404 status code
    """
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{item_name} with ID {id} not found"
        )

def validate_unique_field(
    exists: bool, field_name: str, field_value: Any, item_name: str
) -> None:
    """
    Validate that a field value is unique.
    Raises an HTTPException with appropriate status code if not unique.
    
    Args:
        exists: Boolean indicating if an item with the field value already exists
        field_name: Name of the field being checked (e.g., "email")
        field_value: Value of the field that should be unique
        item_name: Human-readable name of the item type (e.g., "User", "Course")
        
    Raises:
        HTTPException: If exists is True, with 400 status code
    """
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{item_name} with {field_name} '{field_value}' already exists"
        )

def validate_permission(
    has_permission: bool, message: str = "Not enough permissions"
) -> None:
    """
    Validate that the user has permission to perform an action.
    Raises an HTTPException with appropriate status code if not.
    
    Args:
        has_permission: Boolean indicating if user has necessary permissions
        message: Custom error message (defaults to "Not enough permissions")
        
    Raises:
        HTTPException: If has_permission is False, with 403 status code
    """
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

def validate_file_size(file_size: int, max_size: int) -> None:
    """
    Validate that a file size is within the allowed limit.
    Raises an HTTPException with appropriate status code if too large.
    
    Args:
        file_size: Size of the file in bytes
        max_size: Maximum allowed size in bytes
        
    Raises:
        HTTPException: If file_size exceeds max_size, with 413 status code
    """
    if file_size > max_size:
        # Convert bytes to megabytes for human-readable error message
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb:.1f}MB"
        )

def validate_file_type(file_type: str, allowed_types: List[str]) -> None:
    """
    Validate that a file type is allowed.
    Raises an HTTPException with appropriate status code if not allowed.
    
    Args:
        file_type: MIME type or extension of the file
        allowed_types: List of allowed MIME types or extensions
        
    Raises:
        HTTPException: If file_type is not in allowed_types, with 415 status code
    """
    if file_type.lower() not in [t.lower() for t in allowed_types]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )