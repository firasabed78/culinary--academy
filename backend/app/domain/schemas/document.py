"""
Objective: Define data validation and serialization models for document resources.
This file defines the Pydantic models used for validating document-related data
in requests and responses, ensuring type safety and data integrity.


These schema files define the data validation and serialization models used throughout the application. Key features include:

Type Safety: Using Python type hints and Pydantic's validation system to ensure data integrity.
Validation Rules: Fields have constraints like minimum/maximum lengths and custom validators.
Schema Organization:

Base models define common fields shared across schemas
Create models extend base models with fields needed for creation
Update models contain optional fields for partial updates
InDB models represent complete database records including auto-generated fields
Response models define what's returned in API responses


Circular Import Handling: Imports that would cause circular dependencies are done within class definitions rather than at the module level.
ORM Integration: orm_mode = True enables seamless conversion between SQLAlchemy models and Pydantic schemas.
Related Data Models: Extended schemas like WithUser or WithDetails include related entity data for comprehensive API responses.

This approach ensures consistent data validation, clear API contracts, and a clean separation between database models and API representations, all while maintaining type safety throughout the application.
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.domain.models.document import DocumentType  # Import enum from SQLAlchemy model

class DocumentBase(BaseModel):
    """
    Base schema for document data.
    
    Contains common fields that are shared across all document schemas,
    serving as the foundation for more specific document models.
    """
    user_id: int  # The user who owns the document
    document_type: DocumentType  # The type of document (enum)
    description: Optional[str] = None  # Optional document description

class DocumentCreate(DocumentBase):
    """
    Schema for creating a new document.
    
    Extends the base schema with additional fields required when uploading
    a new document, such as file metadata.
    """
    file_name: str = Field(..., min_length=1)  # Required non-empty filename
    file_path: str = Field(..., min_length=1)  # Required non-empty file path
    file_type: Optional[str] = None  # File MIME type
    file_size: Optional[int] = None  # File size in bytes

class DocumentUpdate(BaseModel):
    """
    Schema for updating a document.
    
    Contains fields that can be updated after document creation.
    All fields are optional as updates may only change specific fields.
    """
    document_type: Optional[DocumentType] = None  # New document type
    description: Optional[str] = None  # New description

class DocumentInDB(DocumentBase):
    """
    Schema for document in database.
    
    Complete document model matching the database schema,
    including auto-generated fields like IDs and timestamps.
    """
    id: int  # Database primary key
    file_name: str  # Document filename
    file_path: str  # Path to the file on the server
    file_type: Optional[str] = None  # File MIME type
    upload_date: datetime  # When the document was uploaded
    file_size: Optional[int] = None  # File size in bytes
    created_at: datetime  # Record creation timestamp
    updated_at: datetime  # Record last update timestamp
    
    class Config:
        orm_mode = True  # Enable ORM mode for SQLAlchemy integration

class Document(DocumentInDB):
    """
    Schema for document API response.
    
    The primary model used for API responses containing document data.
    Inherits all fields from DocumentInDB.
    """
    pass

class DocumentWithUser(Document):
    """
    Schema for document with user details.
    
    Extended document model that includes the associated user's information,
    typically used for detailed document views.
    """
    from app.domain.schemas.user import User  # Import needed here to avoid circular imports
    user: User  # The user who owns the document