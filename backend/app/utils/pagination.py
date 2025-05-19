"""
pagination.py - Pagination utility for API endpoints
This file provides reusable pagination components for FastAPI endpoints,
including parameter validation, pagination calculation, and standardized
response formatting. It enables consistent pagination behavior across
the API and simplifies implementation in route handlers by abstracting
pagination logic.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar  # Import typing utilities for type hints
from fastapi import Query  # Import FastAPI Query for parameter validation
from pydantic import BaseModel  # Import Pydantic base model for response schemas
from sqlalchemy.orm import Query as SQLAlchemyQuery  # Import SQLAlchemy Query type for type annotations

# Define generic type variable for model instances
ModelType = TypeVar("ModelType")  # Type variable representing database models

class PaginationParams:
    """Class for pagination parameters."""
    
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),  # Starting offset, must be non-negative
        limit: int = Query(100, ge=1, le=100, description="Number of items to return"),  # Page size, between 1-100
    ):
        # Store validated parameters
        self.skip = skip    # Number of records to skip (offset)
        self.limit = limit  # Maximum number of records to return (page size)

class Page(Generic[ModelType]):
    """
    Pagination response model.
    Provides a standardized structure for paginated API responses.
    """
    
    def __init__(
        self,
        items: List[ModelType],  # List of items for the current page
        total: int,              # Total number of items across all pages
        page: int,               # Current page number (1-indexed)
        size: int,               # Number of items per page
    ):
        # Primary data
        self.items = items  # List of items for the current page
        self.total = total  # Total number of items across all pages
        self.page = page    # Current page number
        self.size = size    # Number of items per page
        
        # Derived pagination metadata
        self.pages = (total + size - 1) // size if size > 0 else 0  # Calculate total number of pages (ceiling division)
        self.has_previous = page > 1  # Whether there's a previous page available
        self.has_next = page < self.pages  # Whether there's a next page available

def paginate(
    query: SQLAlchemyQuery,
    params: PaginationParams
) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object to paginate
        params: Pagination parameters (skip and limit)
        
    Returns:
        Dict with pagination information and items:
        - items: List of records for the current page
        - total: Total number of records matching the query
        - page: Current page number (1-indexed)
        - size: Page size
        - pages: Total number of pages
        - has_previous: Whether a previous page exists
        - has_next: Whether a next page exists
    """
    # Get total count of items without pagination
    total = query.count()
    
    # Apply pagination to query
    items = query.offset(params.skip).limit(params.limit).all()
    
    # Calculate page number (1-indexed)
    page = (params.skip // params.limit) + 1 if params.limit > 0 else 1
    
    # Return standardized pagination response
    return {
        "items": items,  # List of records for the current page
        "total": total,  # Total number of records matching the query
        "page": page,    # Current page number (1-indexed)
        "size": params.limit,  # Page size
        "pages": (total + params.limit - 1) // params.limit if params.limit > 0 else 0,  # Total pages (ceiling division)
        "has_previous": page > 1,  # Whether there's a previous page
        "has_next": page < ((total + params.limit - 1) // params.limit if params.limit > 0 else 0)  # Whether there's a next page
    }