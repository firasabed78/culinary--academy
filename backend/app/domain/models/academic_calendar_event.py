from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base_class import Base


class AcademicCalendarEvent(Base):
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    start_datetime = Column(DateTime, default=datetime.utcnow)
    end_datetime = Column(DateTime, default=datetime.utcnow)
