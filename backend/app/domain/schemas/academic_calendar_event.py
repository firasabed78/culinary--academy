from typing import Optional
from datetime import datetime

from pydantic import BaseModel


# Shared properties
class AcademicCalendarEventBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None


# Properties to receive on item creation
class AcademicCalendarEventCreate(AcademicCalendarEventBase):
    title: str
    start_datetime: datetime
    end_datetime: datetime


# Properties to receive on item update
class AcademicCalendarEventUpdate(AcademicCalendarEventBase):
    pass


# Properties shared by models stored in DB
class AcademicCalendarEventInDBBase(AcademicCalendarEventBase):
    id: int
    title: str
    start_datetime: datetime
    end_datetime: datetime

    class Config:
        orm_mode = True


# Properties to return to client
class AcademicCalendarEvent(AcademicCalendarEventInDBBase):
    pass


# Properties properties stored in DB
class AcademicCalendarEventInDB(AcademicCalendarEventInDBBase):
    pass
