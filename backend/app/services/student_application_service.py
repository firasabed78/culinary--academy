from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import date

from app.db.base_class import Base
from app.domain.models.student_application import StudentApplication
from app.domain.schemas.student_application import StudentApplicationCreate, StudentApplicationUpdate
from app.repositories.student_application_repository import StudentApplicationRepository


class StudentApplicationService:
    def __init__(self, db: Session):
        self.student_application_repository = StudentApplicationRepository(db)

    def get(self, id: Any) -> Optional[StudentApplication]:
        return self.student_application_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[StudentApplication]:
        return self.student_application_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: StudentApplicationCreate) -> StudentApplication:
        return self.student_application_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[StudentApplicationUpdate, Dict[str, Any]]
    ) -> StudentApplication:
        application = self.get(id)
        return self.student_application_repository.update(db_obj=application, obj_in=obj_in)

    def remove(self, id: int) -> StudentApplication:
        return self.student_application_repository.remove(id)
