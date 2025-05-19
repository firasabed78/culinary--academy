from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.grading import Grading
from app.domain.schemas.grading import GradingCreate, GradingUpdate


class GradingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: Any) -> Optional[Grading]:
        return self.db.query(Grading).filter(Grading.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Grading]:
        return self.db.query(Grading).offset(skip).limit(limit).all()

    def create(self, obj_in: GradingCreate) -> Grading:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = Grading(**obj_in_data)  # type: ignore
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: Grading,
        obj_in: Union[GradingUpdate, Dict[str, Any]],
    ) -> Grading:
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def remove(self, id: int) -> Grading:
        obj = self.db.query(Grading).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
