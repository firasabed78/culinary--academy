from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.academic_calendar_event import AcademicCalendarEvent
from app.domain.schemas.academic_calendar_event import AcademicCalendarEventCreate, AcademicCalendarEventUpdate


class AcademicCalendarEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, id: Any) -> Optional[AcademicCalendarEvent]:
        return self.db.query(AcademicCalendarEvent).filter(AcademicCalendarEvent.id == id).first()

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[AcademicCalendarEvent]:
        return self.db.query(AcademicCalendarEvent).offset(skip).limit(limit).all()

    def create(self, obj_in: AcademicCalendarEventCreate) -> AcademicCalendarEvent:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = AcademicCalendarEvent(**obj_in_data)  # type: ignore
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db_obj: AcademicCalendarEvent,
        obj_in: Union[AcademicCalendarEventUpdate, Dict[str, Any]],
    ) -> AcademicCalendarEvent:
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

    def remove(self, id: int) -> AcademicCalendarEvent:
        obj = self.db.query(AcademicCalendarEvent).get(id)
        self.db.delete(obj)
        self.db.commit()
        return obj
