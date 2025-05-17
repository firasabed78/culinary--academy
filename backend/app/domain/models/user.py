"""
user.py - User model definition
This file defines the SQLAlchemy ORM model for users in the learning management system.
It includes user roles (student, instructor, admin), authentication information,
personal details, and establishes relationships with other entities like courses,
enrollments, documents, and notifications. The user model serves as the central
identity and access control mechanism for the system.
"""

from sqlalchemy import Boolean, Column, String, Integer, Enum, Text  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
import enum  # Import Python's enum module for role definitions
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class UserRole(str, enum.Enum):
    """
    Enumeration of user roles in the system.
    Defines the access levels and capabilities of users.
    """
    STUDENT = "student"       # Regular learners who can enroll in courses
    INSTRUCTOR = "instructor" # Teachers who can create and manage courses
    ADMIN = "admin"           # System administrators with full access

class User(Base):
    """User accounts for authentication and profile management."""
    __tablename__ = "users"  # Database table name for users
    
    # Primary key and authentication fields
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    email = Column(String(255), unique=True, index=True, nullable=False)  # Email address (used as username) with uniqueness constraint
    hashed_password = Column(String(255), nullable=False)  # Securely hashed password (never stored in plaintext)
    
    # User profile information
    full_name = Column(String(255), nullable=False)  # User's full name
    role = Column(Enum(UserRole), nullable=False)  # User's role/access level in the system
    phone = Column(String(20), nullable=True)  # Contact phone number (optional)
    address = Column(Text, nullable=True)  # Physical address (optional)
    is_active = Column(Boolean, default=True)  # Account status flag (inactive accounts cannot login)
    profile_picture = Column(String(255), nullable=True)  # Path or URL to profile image (optional)
    
    # Relationships with other entities
    courses = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")  # Courses taught by user (if instructor)
    enrollments = relationship("Enrollment", back_populates="student", foreign_keys="Enrollment.student_id")  # Course enrollments (if student)
    documents = relationship("Document", back_populates="user")  # User's uploaded documents
    notifications = relationship("Notification", back_populates="user")  # Notifications sent to user
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration