from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
import os
import uuid
import shutil
from fastapi import UploadFile

from app.domain.models.document import Document, DocumentType
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.repositories.document_repository import DocumentRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.config import settings


class DocumentService(BaseService[Document, DocumentCreate, DocumentUpdate, DocumentRepository]):
    """Service for document operations."""
    
    def __init__(self):
        super().__init__(DocumentRepository)
        self.upload_dir = settings.UPLOAD_DIR
        self.max_size = settings.MAX_UPLOAD_SIZE  # 5MB default
        self.allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    
    def get_with_user(self, db: Session, id: int) -> Optional[Document]:
        """Get a document with user data."""
        document = self.repository.get_with_user(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        return document
    
    async def upload_document(
        self, db: Session, *, file: UploadFile, document_type: DocumentType, 
        user_id: int, description: Optional[str] = None
    ) -> Document:
        """Upload a new document."""
        # Validate file size
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        await file.seek(0)
        
        if file_size > self.max_size:
            raise ValidationError(detail=f"File too large. Maximum size is {self.max_size / (1024 * 1024)}MB")
        
        # Validate file extension
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in self.allowed_extensions:
            raise ValidationError(
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Create user upload directory if it doesn't exist
        user_upload_dir = os.path.join(self.upload_dir, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        document_data = DocumentCreate(
            user_id=user_id,
            document_type=document_type,
            description=description,
            file_name=file.filename,
            file_path=file_path,
            file_type=ext.replace('.', ''),
            file_size=file_size
        )
        
        return self.repository.create(db, obj_in=document_data)
    
    def get_document_file(self, db: Session, *, id: int) -> Optional[Dict[str, Any]]:
        """Get document file information."""
        document = self.repository.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        if not os.path.exists(document.file_path):
            raise NotFoundError(detail="Document file not found")
        
        return {
            "file_path": document.file_path,
            "file_name": document.file_name,
            "file_type": document.file_type
        }
    
    def delete_document(self, db: Session, *, id: int) -> Document:
        """Delete a document and its file."""
        document = self.repository.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        # Delete file if it exists
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Remove from database
        return self.repository.remove(db, id=id)
    
    def get_user_documents(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get all documents for a user."""
        return self.repository.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def get_documents_by_type(
        self, db: Session, *, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get documents by type."""
        return self.repository.get_by_document_type(db, document_type=document_type, skip=skip, limit=limit)
    
    def get_filtered_documents(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Document]:
        """Get documents with filtering."""
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)