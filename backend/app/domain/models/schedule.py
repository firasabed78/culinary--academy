"""
schedule.py - Schedule model definition
This file defines the SQLAlchemy ORM model for course schedules in the learning 
management system. It tracks when and where courses are held, including time slots,
location information, and recurrence patterns. The schedule model enforces business
rules through constraints such as ensuring end times are after start times and
validating day of week values.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, Date, Time, Boolean, CheckConstraint  # Import SQLAlchemy column types and constraints
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
import enum  # Import Python's enum module (used for type consistency with other models)
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class Schedule(Base):
    """Course schedule records."""
    __tablename__ = "schedules"  # Database table name for schedules
    
    # Primary key and relationship IDs
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)  # Foreign key to the associated course
    
    # Schedule timing details
    day_of_week = Column(Integer, CheckConstraint("day_of_week >= 0 AND day_of_week <= 6"), nullable=False)  # Day of week (0=Sunday, 6=Saturday) with valid range constraint
    start_time = Column(Time, nullable=False)  # Start time of the class/session
    end_time = Column(Time, nullable=False)  # End time of the class/session
    
    # Location and recurrence information
    location = Column(String(255), nullable=True)  # Physical or virtual location of the class
    is_recurring = Column(Boolean, default=True, nullable=False)  # Whether schedule repeats weekly
    
    # Date range for the schedule
    start_date = Column(Date, nullable=True)  # First date when the schedule becomes effective
    end_date = Column(Date, nullable=True)  # Last date when the schedule is effective
    
    # Schedule status
    is_active = Column(Boolean, default=True)  # Flag indicating if the schedule is currently active
    
    # Table-level constraints
    __table_args__ = (
        # Ensure logical time sequence (end time must be after start time)
        CheckConstraint('end_time > start_time', name='check_end_time_after_start_time'),
    )
    
    # Relationships
    course = relationship("Course", back_populates="schedules")  # Bi-directional relationship with Course model
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration