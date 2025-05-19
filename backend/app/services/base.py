"""
Objective: Define a foundational service layer for business logic operations.
This file implements a generic base service class that encapsulates common
business logic operations, delegating data access to the repository layer.

The BaseService class implements the Service Layer pattern in your application's architecture, providing a clear separation between business logic and data access.
Key Features:

Service Layer Pattern:

Business Logic Abstraction: Encapsulates and centralizes business logic
Repository Delegation: Delegates data access operations to repositories
Generic Implementation: Works with any model/schema/repository combination
Error Handling: Adds additional error checking before operations


Key Operations:

Entity Retrieval: Single or multiple entity fetching with filters
Entity Creation: Creating new entities with validation
Entity Updates: Modifying existing entities after existence check
Entity Deletion: Removing entities after existence check


Design Considerations:

Existence Checks: Verifying entities exist before updates/deletes
Type Safety: Using generics for type consistency
Clean API: Simple, consistent methods for business operations
Separation of Concerns: Clear distinction from data access layer



Architecture Roles:
This service layer plays a critical role in your application's architecture:

Mediates Between API and Data Access: Sits between API controllers and repositories
Centralizes Business Rules: Provides a place for business logic implementation
Abstracts Data Operations: Shields controllers from direct data access concerns
Enables Testing: Facilitates unit testing of business logic in isolation

Benefits:
The service layer provides several important benefits:

Maintainability: Business logic is centralized rather than scattered
Testability: Services can be tested independently of repositories
Code Organization: Clear separation of responsibilities
Flexibility: Services can combine operations from multiple repositories
Consistency: Common error handling and validation across operations

This base service class serves as a foundation for more specialized service classes that will implement domain-specific business logic while leveraging the common CRUD operations provided here. Those specialized services will extend this base class and add domain-specific methods.
The service layer is a crucial part of your application's architecture, providing a clear place for business rules and domain logic while delegating data access to repositories. This separation creates a more maintainable and testable codebase as the application grows in complexity.

"""
"""
base.py - Base service class for business logic
This file defines the foundation for service classes that implement
business logic for the Culinary Academy Student Registration system.
It provides a standard interface for interacting with CRUD operations.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.core.exceptions import NotFoundError

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
CRUDType = TypeVar("CRUDType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, CRUDType]):
    """
    Base class for service operations with a specific model, providing 
    standard business logic that uses CRUD operations.
    """
    
    def __init__(self, crud_class: CRUDType):
        """
        Initialize service with a CRUD class.
        
        Parameters
        ----------
        crud_class: CRUD class for database operations
        """
        self.crud = crud_class
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Primary key value
        
        Returns
        -------
        Optional[ModelType]
            The model instance if found, None otherwise
        """
        return self.crud.get(db, id)
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Get multiple records with pagination.
        
        Parameters
        ----------
        db: SQLAlchemy session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[ModelType]
            List of model instances
        """
        return self.crud.get_multi(db, skip=skip, limit=limit)
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Pydantic model with create data
        
        Returns
        -------
        ModelType
            The created model instance
        """
        return self.crud.create(db, obj_in=obj_in)
    
    def update(
        self,
        db: Session,
        *,
        id: Any,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Primary key value
        obj_in: Update data, either as Pydantic model or dict
        
        Returns
        -------
        ModelType
            The updated model instance
            
        Raises
        ------
        NotFoundError
            If record with the given ID is not found
        """
        db_obj = self.crud.get(db, id)
        if not db_obj:
            raise NotFoundError(detail=f"Record with ID {id} not found")
        return self.crud.update(db, db_obj=db_obj, obj_in=obj_in)
    
    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Remove a record.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Primary key value
        
        Returns
        -------
        ModelType
            The removed model instance
            
        Raises
        ------
        NotFoundError
            If record with the given ID is not found
        """
        db_obj = self.crud.get(db, id)
        if not db_obj:
            raise NotFoundError(detail=f"Record with ID {id} not found")
        return self.crud.remove(db, id=id)