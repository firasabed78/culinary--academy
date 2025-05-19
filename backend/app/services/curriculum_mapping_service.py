from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.curriculum_mapping import CurriculumMapping
from app.domain.schemas.curriculum_mapping import CurriculumMappingCreate, CurriculumMappingUpdate
from app.repositories.curriculum_mapping_repository import CurriculumMappingRepository


class CurriculumMappingService:
    def __init__(self, db: Session):
        self.curriculum_mapping_repository = CurriculumMappingRepository(db)

    def get(self, id: Any) -> Optional[CurriculumMapping]:
        return self.curriculum_mapping_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[CurriculumMapping]:
        return self.curriculum_mapping_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: CurriculumMappingCreate) -> CurriculumMapping:
        return self.curriculum_mapping_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[CurriculumMappingUpdate, Dict[str, Any]]
    ) -> CurriculumMapping:
        mapping = self.get(id)
        return self.curriculum_mapping_repository.update(db_obj=mapping, obj_in=obj_in)

    def remove(self, id: int) -> CurriculumMapping:
        return self.curriculum_mapping_repository.remove(id)
