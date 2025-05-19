from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base
from app.domain.models.academic_calendar_event import AcademicCalendarEvent
from app.domain.schemas.academic_calendar_event import AcademicCalendarEventCreate, AcademicCalendarEventUpdate
from app.repositories.academic_calendar_event_repository import AcademicCalendarEventRepository


class AcademicCalendarEventService:
    def __init__(self, db: Session):
        self.academic_calendar_event_repository = AcademicCalendarEventRepository(db)

    def get(self, id: Any) -> Optional[AcademicCalendarEvent]:
        return self.academic_calendar_event_repository.get(id)

    def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[AcademicCalendarEvent]:
        return self.academic_calendar_event_repository.get_multi(skip=skip, limit=limit)

    def create(self, obj_in: AcademicCalendarEventCreate) -> AcademicCalendarEvent:
        return self.academic_calendar_event_repository.create(obj_in=obj_in)

    def update(
        self, id: int, obj_in: Union[AcademicCalendarEventUpdate, Dict[str, Any]]
    ) -> AcademicCalendarEvent:
        event = self.get(id)
        return self.academic_calendar_event_repository.update(db_obj=event, obj_in=obj_in)

    def remove(self, id: int) -> AcademicCalendarEvent:
        return self.academic_calendar_event_repository.remove(id)
