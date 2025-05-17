"""
Objective: Implement specialized business logic for document management.
This file extends the base service with document-specific operations,
including file uploads, storage, retrieval, and validation.


The DocumentService class is a specialized service that handles the business logic for document management, particularly focusing on file uploads, storage, and retrieval.
Key Features:

File Management Operations:

File Upload: Handling file uploads with validation
File Storage: Saving files to the filesystem with unique names
File Retrieval: Getting file information for serving to users
File Deletion: Removing files from both filesystem and database


Validation Logic:

Size Validation: Enforcing maximum file size limits
Type Validation: Restricting uploads to allowed file extensions
Existence Checks: Verifying files exist before operations


Storage Organization:

User Directories: Organizing files by user ID
Unique Filenames: Preventing filename collisions with UUIDs
Path Management: Handling file paths between database and filesystem


Business Rules:

Document Classification: Supporting different document types
Metadata Tracking: Storing file metadata with documents
User Association: Linking documents to their owners



Technical Implementation Details:

File System Interaction:

Creating directories with os.makedirs
Saving files with shutil.copyfileobj
Checking file existence with os.path.exists
Removing files with os.remove


Asynchronous File Handling:

Using async/await for file operations
Reading file content with await file.read()
Resetting file position with await file.seek(0)


Error Handling:

Raising NotFoundError for missing documents or files
Raising ValidationError for invalid file size or type
Providing descriptive error messages


Security Considerations:

Using UUIDs for filenames to prevent guessing
Validating file types to prevent unsafe uploads
Limiting file sizes to prevent denial of service



This service demonstrates the integration of file system operations with database management, showing how the service layer can handle complex business logic that goes beyond simple CRUD operations. It effectively bridges the gap between the HTTP layer (which receives file uploads) and the repository layer (which manages database records), while also handling the file system interactions that are unique to document management.
The service follows best practices for file storage and validation, ensuring both security and reliability in document handling.

"""

from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
import os
import uuid  # For generating unique filenames
import shutil
from fastapi import UploadFile  # FastAPI's file upload type

from app.domain.models.document import Document, DocumentType
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.repositories.document_repository import DocumentRepository
from app.services.base import BaseService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.config import settings  # Application settings


class DocumentService(BaseService[Document, DocumentCreate, DocumentUpdate, DocumentRepository]):
    """
    Service for document operations.
    
    Extends the base service with document-specific business logic,
    handling file uploads, storage, retrieval, and validation.
    """
    
    def __init__(self):
        """
        Initialize the document service.
        
        Sets up the service with document-specific configuration from settings,
        including upload directory, file size limits, and allowed file types.
        """
        super().__init__(DocumentRepository)
        self.upload_dir = settings.UPLOAD_DIR  # Base directory for uploads
        self.max_size = settings.MAX_UPLOAD_SIZE  # Maximum file size (e.g., 5MB)
        self.allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']  # Allowed file types
    
    def get_with_user(self, db: Session, id: int) -> Optional[Document]:
        """
        Get a document with user data.
        
        Retrieves a document with its owner's information,
        raising an exception if not found.
        
        Args:
            db: SQLAlchemy database session
            id: Document ID
            
        Returns:
            Document with user data
            
        Raises:
            NotFoundError: If document doesn't exist
        """
        document = self.repository.get_with_user(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        return document
    
    async def upload_document(
        self, db: Session, *, file: UploadFile, document_type: DocumentType, 
        user_id: int, description: Optional[str] = None
    ) -> Document:
        """
        Upload a new document.
        
        Handles file upload, validation, storage, and database record creation.
        This method manages both the file system operations and the database record.
        
        Args:
            db: SQLAlchemy database session
            file: The uploaded file
            document_type: Type of document being uploaded
            user_id: ID of the user uploading the document
            description: Optional description of the document
            
        Returns:
            Created document record
            
        Raises:
            ValidationError: If file size or type is invalid
        """
        # Validate file size by reading contents
        file_size = 0
        contents = await file.read()  # Read file into memory
        file_size = len(contents)  # Get file size
        await file.seek(0)  # Reset file pointer for later use
        
        # Check if file exceeds maximum size
        if file_size > self.max_size:
            raise ValidationError(detail=f"File too large. Maximum size is {self.max_size / (1024 * 1024)}MB")
        
        # Extract and validate file extension
        _, ext = os.path.splitext(file.filename)
        if ext.lower() not in self.allowed_extensions:
            raise ValidationError(
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Create user-specific upload directory
        user_upload_dir = os.path.join(self.upload_dir, str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        # Generate unique filename to prevent collisions
        unique_filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # Save file to filesystem
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record in database
        document_data = DocumentCreate(
            user_id=user_id,
            document_type=document_type,
            description=description,
            file_name=file.filename,  # Original filename
            file_path=file_path,      # Storage path
            file_type=ext.replace('.', ''),  # File extension without dot
            file_size=file_size       # File size in bytes
        )
        
        return self.repository.create(db, obj_in=document_data)
    
    def get_document_file(self, db: Session, *, id: int) -> Optional[Dict[str, Any]]:
        """
        Get document file information.
        
        Retrieves file metadata needed for serving the file to users,
        checking both database record and file existence.
        
        Args:
            db: SQLAlchemy database session
            id: Document ID
            
        Returns:
            Dictionary with file path, name, and type
            
        Raises:
            NotFoundError: If document or file doesn't exist
        """
        # Get document record
        document = self.repository.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        # Verify file exists on filesystem
        if not os.path.exists(document.file_path):
            raise NotFoundError(detail="Document file not found")
        
        # Return file information
        return {
            "file_path": document.file_path,
            "file_name": document.file_name,
            "file_type": document.file_type
        }
    
    def delete_document(self, db: Session, *, id: int) -> Document:
        """
        Delete a document and its file.
        
        Removes both the file from the filesystem and the document record
        from the database.
        
        Args:
            db: SQLAlchemy database session
            id: Document ID
            
        Returns:
            Deleted document record
            
        Raises:
            NotFoundError: If document doesn't exist
        """
        # Get document record
        document = self.repository.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        # Delete file from filesystem if it exists
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Remove database record
        return self.repository.remove(db, id=id)
    
    def get_user_documents(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get all documents for a user.
        
        Retrieves documents owned by a specific user with pagination.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents owned by the user
        """
        return self.repository.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def get_documents_by_type(
        self, db: Session, *, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by type.
        
        Retrieves documents of a specific type with pagination.
        
        Args:
            db: SQLAlchemy database session
            document_type: Document type to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents of the specified type
        """
        return self.repository.get_by_document_type(db, document_type=document_type, skip=skip, limit=limit)
    
    def get_filtered_documents(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Document]:
        """
        Get documents with filtering.
        
        Retrieves documents matching various filter criteria with pagination.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Filter criteria
            
        Returns:
            List of documents matching the filter criteria
        """
        return self.repository.get_multi_by_filters(db, skip=skip, limit=limit, **filters)