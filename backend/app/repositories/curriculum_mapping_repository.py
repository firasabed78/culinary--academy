from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.curriculum_mapping import CurriculumMapping
from app.domain.schemas.curriculum_mapping import CurriculumMappingCreate, CurriculumMappingUpdate


class CurriculumMappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: Any) -> Optional[CurriculumMapping]:
        return self.db.query(CurriculumMapping).filter(CurriculumMapping.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[CurriculumMapping]:
        return self.db.query(CurriculumMapping).offset(skip).limit(limit).all()

    def create(self, obj_in: CurriculumMappingCreate) -> CurriculumMapping:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = CurriculumMapping(**obj_in_data)  # type: ignore
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: CurriculumMapping,
        obj_in: Union[CurriculumMappingUpdate, Dict[str, Any]],
    ) -> CurriculumMapping:
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

    def remove(self, id: int) -> CurriculumMapping:
        obj = self.db.query(CurriculumMapping).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
