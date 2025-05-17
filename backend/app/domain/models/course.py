"""
course.py - Course model definition
This file defines the SQLAlchemy ORM model for courses in the learning management system.
It specifies the database structure, relationships with other entities like users,
enrollments, and schedules, and includes attributes for course details such as
title, description, pricing, duration, and capacity.
"""

from sqlalchemy import Boolean, Column, String, Integer, Float, ForeignKey, Date, Text  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for defining model associations
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class Course(Base):
    """
    Course model represents educational courses offered in the system.
    Courses are taught by instructors, have schedules, and can be enrolled in by students.
    """
    __tablename__ = "courses"  # Database table name for courses
    
    # Primary key and basic course information
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    title = Column(String(255), nullable=False, index=True)  # Course title with index for searching
    description = Column(Text, nullable=True)  # Course description, allowing for lengthy content
    
    # Instructor relationship
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Foreign key linking to instructor's user ID
    
    # Course details
    duration = Column(Integer, nullable=False)  # Course duration in days
    price = Column(Float, nullable=False)  # Course price
    capacity = Column(Integer, nullable=False)  # Maximum number of students
    
    # Course timeline
    start_date = Column(Date, nullable=True)  # Start date of the course
    end_date = Column(Date, nullable=True)  # End date of the course
    
    # Status and display
    is_active = Column(Boolean, default=True)  # Flag indicating if course is currently active
    image_url = Column(String(255), nullable=True)  # URL to course image for UI display
    
    # Relationships with other entities
    instructor = relationship("User", back_populates="courses", foreign_keys=[instructor_id])  # Bi-directional relationship with User model
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")  # Student enrollments with cascade delete
    schedules = relationship("Schedule", back_populates="course", cascade="all, delete-orphan")  # Course schedule entries with cascade delete
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration