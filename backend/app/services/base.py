# backend/app/services/base.py
from typing import Generic, TypeVar, List, Optional, Type, Any, Union, Dict
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.base_class import Base
from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType, RepositoryType]):
    """
    Base service providing business logic operations.
    """
    def __init__(self, repository: Type[RepositoryType]):
        self.repository = repository()

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.repository.get(db, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[ModelType]:
        """Get multiple records with pagination and filters."""
        return self.repository.get_multi(db, skip=skip, limit=limit, **filters)

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        return self.repository.create(db, obj_in=obj_in)

    def update(
        self, db: Session, *, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> Optional[ModelType]:
        """Update a record."""
        db_obj = self.repository.get(db, id)
        if db_obj:
            return self.repository.update(db, db_obj=db_obj, obj_in=obj_in)
        return None

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Delete a record."""
        db_obj = self.repository.get(db, id)
        if db_obj:
            return self.repository.remove(db, id=id)
        return None