from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime

from app.domain.models.document import DocumentType


class DocumentBase(BaseModel):
    """Base schema for document data."""
    user_id: int
    document_type: DocumentType
    description: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    file_name: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
    file_type: Optional[str] = None
    file_size: Optional[int] = None


class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    document_type: Optional[DocumentType] = None
    description: Optional[str] = None


class DocumentInDB(DocumentBase):
    """Schema for document in database."""
    id: int
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    upload_date: datetime
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class Document(DocumentInDB):
    """Schema for document API response."""
    pass


class DocumentWithUser(Document):
    """Schema for document with user details."""
    from app.domain.schemas.user import User

    user: User