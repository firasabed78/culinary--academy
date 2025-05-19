from fastapi import APIRouter, Depends
from typing import Any, List

router = APIRouter()


@router.get("/", response_model=List[Any])
def read_programs() -> Any:
    """
    Retrieve programs.
    """
    return []


@router.post("/", response_model=Any)
def create_program() -> Any:
    """
    Create new program.
    """
    return {}


@router.get("/{id}", response_model=Any)
def read_program(id: int) -> Any:
    """
    Get program by ID.
    """
    return {}


@router.put("/{id}", response_model=Any)
def update_program(id: int) -> Any:
    """
    Update a program.
    """
    return {}


@router.delete("/{id}", response_model=Any)
def delete_program(id: int) -> Any:
    """
    Delete a program.
    """
    return {}
