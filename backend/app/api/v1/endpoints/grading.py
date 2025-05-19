from fastapi import APIRouter, Depends
from typing import Any, List

router = APIRouter()


@router.get("/", response_model=List[Any])
def read_gradings() -> Any:
    """
    Retrieve gradings.
    """
    return []


@router.post("/", response_model=Any)
def create_grading() -> Any:
    """
    Create new grading.
    """
    return {}


@router.get("/{id}", response_model=Any)
def read_grading(id: int) -> Any:
    """
    Get grading by ID.
    """
    return {}


@router.put("/{id}", response_model=Any)
def update_grading(id: int) -> Any:
    """
    Update a grading.
    """
    return {}


@router.delete("/{id}", response_model=Any)
def delete_grading(id: int) -> Any:
    """
    Delete a grading.
    """
    return {}
