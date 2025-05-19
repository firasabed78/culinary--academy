from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.program import Program
from app.domain.schemas.program import ProgramCreate, ProgramUpdate
from app.repositories.program_repository import ProgramRepository


class ProgramService:
    def __init__(self, db: Session):
        self.program_repository = ProgramRepository(db)

    def get(self, id: Any) -> Optional[Program]:
        return self.program_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[Program]:
        return self.program_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: ProgramCreate) -> Program:
        return self.program_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[ProgramUpdate, Dict[str, Any]]
    ) -> Program:
        program = self.get(id)
        return self.program_repository.update(db_obj=program, obj_in=obj_in)

    def remove(self, id: int) -> Program:
        return self.program_repository.remove(id)
