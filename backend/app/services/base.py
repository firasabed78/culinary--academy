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

from typing import Generic, TypeVar, List, Optional, Type, Any, Union, Dict
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.base_class import Base
from app.repositories.base import BaseRepository

# Type variables for generic typing
ModelType = TypeVar("ModelType", bound=Base)  # SQLAlchemy model type
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # Creation schema type
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # Update schema type
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)  # Repository type

class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]):
    """
    Base service providing business logic operations.
    
    This generic class implements standard business logic operations
    while delegating data access to the repository layer, following
    the Service pattern to separate business logic from data access.
    """
    
    def __init__(self, repository: Type[RepositoryType]):
        """
        Initialize service with a specific repository type.
        
        Args:
            repository: The repository class this service will use for data access
        """
        self.repository = repository()  # Create an instance of the repository
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Retrieves a specific entity from the repository by its ID.
        
        Args:
            db: SQLAlchemy database session
            id: Primary key value to look up
            
        Returns:
            The found record or None if not found
        """
        return self.repository.get(db, id)
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filters.
        
        Retrieves a paginated list of entities from the repository
        with optional filtering criteria.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Field name/value pairs for filtering
            
        Returns:
            List of matching records
        """
        return self.repository.get_multi(db, skip=skip, limit=limit, **filters)
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Creates a new entity using the repository.
        
        Args:
            db: SQLAlchemy database session
            obj_in: Pydantic model with data for the new record
            
        Returns:
            The created record
        """
        return self.repository.create(db, obj_in=obj_in)
    
    def update(
        self, db: Session, *, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """
        Update a record.
        
        Updates an existing entity with new data after confirming it exists.
        
        Args:
            db: SQLAlchemy database session
            id: Primary key of the record to update
            obj_in: Pydantic model or dict with update data
            
        Returns:
            The updated record or None if not found
        """
        # First check if the object exists
        db_obj = self.repository.get(db, id)
        if db_obj:
            # If it exists, update it
            return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
        return None  # Return None if object doesn't exist
    
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """
        Delete a record.
        
        Deletes an entity after confirming it exists.
        
        Args:
            db: SQLAlchemy database session
            id: Primary key of the record to delete
            
        Returns:
            The deleted record or None if not found
        """
        # First check if the object exists
        db_obj = self.repository.get(db, id)
        if db_obj:
            # If it exists, remove it
            return self.repository.remove(db, id=id)
        return None  # Return None if object doesn't exist