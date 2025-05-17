from sqlalchemy import Column, Integer, ForeignKey, String, Date, Time, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class Schedule(Base):
    """Course schedule records."""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(Integer, CheckConstraint("day_of_week >= 0 AND day_of_week <= 6"), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    location = Column(String(255), nullable=True)
    is_recurring = Column(Boolean, default=True, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Add check constraint to ensure end_time is after start_time
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_end_time_after_start_time'),
    )
    
    # Relationships
    course = relationship("Course", back_populates="schedules")
    
    class Config:
        orm_mode = True