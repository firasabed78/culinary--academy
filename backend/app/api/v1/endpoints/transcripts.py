from fastapi import APIRouter, Depends
from typing import Any, List

router = APIRouter()


@router.get("/", response_model=List[Any])
def read_transcripts() -> Any:
    """
    Retrieve transcripts.
    """
    return []


@router.post("/", response_model=Any)
def create_transcript() -> Any:
    """
    Create new transcript.
    """
    return {}


@router.get("/{id}", response_model=Any)
def read_transcript(id: int) -> Any:
    """
    Get transcript by ID.
    """
    return {}


@router.put("/{id}", response_model=Any)
def update_transcript(id: int) -> Any:
    """
    Update a transcript.
    """
    return {}


@router.delete("/{id}", response_model=Any)
def delete_transcript(id: int) -> Any:
    """
    Delete a transcript.
    """
    return {}
