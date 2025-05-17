from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from fastapi import Query
from pydantic import BaseModel
from sqlalchemy.orm import Query as SQLAlchemyQuery

ModelType = TypeVar("ModelType")


class PaginationParams:
    """Class for pagination parameters."""
    
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=100, description="Number of items to return"),
    ):
        self.skip = skip
        self.limit = limit


class Page(Generic[ModelType]):
    """
    Pagination response model.
    """
    
    def __init__(
        self,
        items: List[ModelType],
        total: int,
        page: int,
        size: int,
    ):
        self.items = items
        self.total = total
        self.page = page
        self.size = size
        self.pages = (total + size - 1) // size if size > 0 else 0
        self.has_previous = page > 1
        self.has_next = page < self.pages


def paginate(
    query: SQLAlchemyQuery, 
    params: PaginationParams
) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        params: Pagination parameters
        
    Returns:
        Dict with pagination information and items
    """
    total = query.count()
    
    items = query.offset(params.skip).limit(params.limit).all()
    
    # Calculate page number (1-indexed)
    page = (params.skip // params.limit) + 1 if params.limit > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": params.limit,
        "pages": (total + params.limit - 1) // params.limit if params.limit > 0 else 0,
        "has_previous": page > 1,
        "has_next": page < ((total + params.limit - 1) // params.limit if params.limit > 0 else 0)
    }