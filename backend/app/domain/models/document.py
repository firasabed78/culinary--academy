"""
document.py - Document model definition for user file uploads
This file defines the SQLAlchemy ORM model for user documents in the system.
It includes an enum for document types, tracks file metadata such as size and type,
and establishes relationships with the user model. The document system allows
storing various types of files like ID proofs, certifications, and resumes.
"""

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Enum  # Import SQLAlchemy column types
from sqlalchemy.orm import relationship  # Import SQLAlchemy relationship for model associations
from sqlalchemy.sql import func  # Import SQL functions for default timestamps
import enum  # Import Python's enum module for type definitions
from app.db.base_class import Base  # Import Base class for SQLAlchemy models

class DocumentType(str, enum.Enum):
    """
    Enumeration of supported document types in the system.
    Used to categorize documents for easier management and validation.
    """
    ID_PROOF = "id_proof"  # Identity verification documents
    CERTIFICATION = "certification"  # Professional certifications
    RESUME = "resume"  # CVs and resumes
    TRANSCRIPT = "transcript"  # Academic transcripts and records
    OTHER = "other"  # Miscellaneous document types not fitting other categories

class Document(Base):
    """User document uploads."""
    __tablename__ = "documents"  # Database table name for documents
    
    # Primary key and basic document information
    id = Column(Integer, primary_key=True, index=True)  # Primary key with index for faster lookups
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Foreign key to user who owns the document
    
    # File metadata
    file_name = Column(String(255), nullable=False)  # Original filename of the uploaded document
    file_path = Column(String(500), nullable=False)  # Path where file is stored in the file system or storage service
    file_type = Column(String(50), nullable=True)  # MIME type or file extension to identify file format
    upload_date = Column(DateTime(timezone=True), server_default=func.now())  # Automatic timestamp when document is uploaded
    document_type = Column(Enum(DocumentType), nullable=False)  # Category of document from predefined types
    description = Column(Text, nullable=True)  # Optional description of the document
    file_size = Column(Integer, nullable=True)  # Size of the file in bytes, for storage management
    
    # Relationships
    user = relationship("User", back_populates="documents")  # Bi-directional relationship with User model
    
    class Config:
        """Pydantic configuration for ORM mode compatibility."""
        orm_mode = True  # Enables ORM mode for Pydantic schema integration