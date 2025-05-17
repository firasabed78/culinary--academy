from typing import Any, Dict, List, Optional, Type, TypeVar
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

ModelType = TypeVar("ModelType", bound=BaseModel)


def validate_model(model_class: Type[ModelType], data: Dict[str, Any]) -> ModelType:
    """
    Validate data against a Pydantic model and return the validated model.
    Raises an HTTPException with appropriate status code on validation error.
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = ".".join(str(l) for l in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
        
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Validation error", "errors": errors}
        )


def validate_id_exists(item: Optional[Any], id: int, item_name: str) -> None:
    """
    Validate that an item with the specified ID exists.
    Raises an HTTPException with appropriate status code if not found.
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
    """
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb:.1f}MB"
        )


def validate_file_type(file_type: str, allowed_types: List[str]) -> None:
    """
    Validate that a file type is allowed.
    Raises an HTTPException with appropriate status code if not allowed.
    """
    if file_type.lower() not in [t.lower() for t in allowed_types]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type not allowed. Allowed types: {', '.join(allowed_types)}"
        )