from sqlalchemy import Boolean, Column, String, Integer, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    profile_picture = Column(String(255), nullable=True)
    
    # Relationships
    courses = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")
    documents = relationship("Document", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    class Config:
        orm_mode = True