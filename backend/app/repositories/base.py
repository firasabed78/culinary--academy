"""
Objective: Implement a generic repository pattern for database operations.
This file defines a base repository class that provides common CRUD operations
for all entity types, reducing code duplication and standardizing data access.

The BaseRepository class implements the Repository pattern, providing a consistent interface for data access operations across your application. This is a key part of your application's architecture:
Key Features:

Generic Implementation: The class uses Python's generic types to work with any SQLAlchemy model and corresponding Pydantic schemas.
Standard CRUD Operations:

get: Retrieve a single record by ID
get_by: Retrieve a record by custom field criteria
get_multi: Retrieve multiple records with pagination and filtering
create: Create a new record
update: Update an existing record
remove: Delete a record


Design Patterns:

Repository Pattern: Abstracts database access logic behind a consistent interface
Generic Pattern: Uses type variables to provide type safety across different entity types
Data Mapper Pattern: Transparently converts between domain objects and database records


Type Safety: Leverages Python's typing system to ensure correct usage across different models
Flexibility:

Accepts both Pydantic models and dictionaries for updates
Supports arbitrary filtering criteria
Includes pagination support for listing operations



Benefits:

Code Reuse: Entity-specific repositories can inherit from this base class, reducing duplication
Consistency: Standardizes database operations across the application
Maintainability: Centralizes database access logic, making it easier to modify or optimize
Testability: Provides a clear seam for mocking in unit tests
Separation of Concerns: Isolates data access logic from business logic

This pattern is a fundamental building block in your application's architecture, providing a clean and consistent way to interact with the database across all entity types. Entity-specific repositories can extend this base class with specialized operations while inheriting all the standard CRUD functionality.

"""

from typing import Generic, TypeVar, Type, List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.base_class import Base  # SQLAlchemy base model

# Type variables for generic typing
ModelType = TypeVar("ModelType", bound=Base)  # SQLAlchemy model type
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # Creation schema type
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # Update schema type

class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing common CRUD operations.
    
    This generic class implements standard database operations that can be
    used by all entity repositories, following the Repository pattern to
    abstract database access and provide a consistent interface.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize repository with a specific model type.
        
        Args:
            model: The SQLAlchemy model class this repository will operate on
        """
        self.model = model
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Get a single record by ID.
        
        Args:
            db: SQLAlchemy database session
            id: Primary key value to look up
            
        Returns:
            The found record or None if not found
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_by(self, db: Session, **kwargs) -> Optional[ModelType]:
        """
        Get a single record by arbitrary filters.
        
        Args:
            db: SQLAlchemy database session
            **kwargs: Field name/value pairs to filter by
            
        Returns:
            The first matching record or None if not found
        """
        query = db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filters.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Field name/value pairs to filter by
            
        Returns:
            List of matching records
        """
        query = db.query(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record.
        
        Args:
            db: SQLAlchemy database session
            obj_in: Pydantic model with data for new record
            
        Returns:
            The created record
        """
        obj_in_data = obj_in.dict()  # Convert Pydantic model to dict
        db_obj = self.model(**obj_in_data)  # Create SQLAlchemy model instance
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get generated values (like ID)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record.
        
        Args:
            db: SQLAlchemy database session
            db_obj: Existing database object to update
            obj_in: Pydantic model or dict with update data
            
        Returns:
            The updated record
        """
        obj_data = db_obj.__dict__  # Get current data as dict
        
        # Handle input as either Pydantic model or dict
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)  # Only include set fields
        
        # Update fields that are present in the input
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)  # Add to session
        db.commit()  # Commit transaction
        db.refresh(db_obj)  # Refresh to get updated values
        return db_obj
    
    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Delete a record.
        
        Args:
            db: SQLAlchemy database session
            id: Primary key of record to delete
            
        Returns:
            The deleted record
        """
        obj = db.query(self.model).get(id)  # Get object to delete
        db.delete(obj)  # Mark for deletion
        db.commit()  # Commit transaction
        return obj