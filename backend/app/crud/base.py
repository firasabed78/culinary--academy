"""
base.py - Base CRUD operations
This file defines the foundation for database CRUD operations used throughout
the Culinary Academy Student Registration system. It provides a generic interface
for creating, reading, updating, and deleting database records.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base

# Define generic type variables
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class that provides CRUD operations for any SQLAlchemy model.
    
    This class is designed to be inherited by specific model CRUD classes,
    providing standard database operations while allowing for customization.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Initialize CRUD operations for a specific model.
        
        Parameters
        ----------
        model: SQLAlchemy model class
            The model class that this CRUD instance will operate on
        """
        self.model = model
    
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
        return db.query(self.model).filter(self.model.id == id).first()
    
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
        return db.query(self.model).offset(skip).limit(limit).all()
    
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
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update an existing record.
        
        Parameters
        ----------
        db: SQLAlchemy session
        db_obj: Existing database model instance to update
        obj_in: Update data, either as Pydantic model or dict
        
        Returns
        -------
        ModelType
            The updated model instance
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
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
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj