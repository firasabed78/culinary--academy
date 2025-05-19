from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.grading import Grading
from app.domain.schemas.grading import GradingCreate, GradingUpdate
from app.repositories.grading_repository import GradingRepository


class GradingService:
    def __init__(self, db: Session):
        self.grading_repository = GradingRepository(db)

    def get(self, id: Any) -> Optional[Grading]:
        return self.grading_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Grading]:
        return self.grading_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: GradingCreate) -> Grading:
        return self.grading_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[GradingUpdate, Dict[str, Any]]
    ) -> Grading:
        grading = self.get(id)
        return self.grading_repository.update(db_obj=grading, obj_in=obj_in)

    def remove(self, id: int) -> Grading:
        return self.grading_repository.remove(id)
