from sqlalchemy import Boolean, Column, String, Integer, Float, ForeignKey, Date, Text
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    duration = Column(Integer, nullable=False)  # in days
    price = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    image_url = Column(String(255), nullable=True)
    
    # Relationships
    instructor = relationship("User", back_populates="courses", foreign_keys=[instructor_id])
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="course", cascade="all, delete-orphan")
    
    class Config:
        orm_mode = True