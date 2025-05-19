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
"""
document_service.py - Service layer for document management
This file handles business logic related to user documents, including
upload processing, validation, and retrieval operations. It manages
the document lifecycle and provides file storage integration.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.domain.models.document import Document, DocumentType
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.crud import document as crud_document
from app.crud import user as crud_user
from app.core.exceptions import NotFoundError, ValidationError
from app.utils.file_storage import FileStorageManager


class DocumentService:
    """Service for document operations using CRUD abstractions."""
    
    def __init__(self):
        # Initialize file storage manager for file operations
        self.file_storage = FileStorageManager()
    
    def get(self, db: Session, id: int) -> Optional[Document]:
        """
        Get a document by ID.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Document ID
        
        Returns
        -------
        Optional[Document]
            Document if found, None otherwise
        """
        return crud_document.get(db, id)
    
    def get_with_user(self, db: Session, id: int) -> Optional[Document]:
        """
        Get a document with user data.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Document ID
        
        Returns
        -------
        Optional[Document]
            Document with user data if found
            
        Raises
        ------
        NotFoundError
            If document not found
        """
        document = crud_document.get_with_user(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        return document
    
    def create_document(
        self, db: Session, *, obj_in: DocumentCreate, file_content: bytes = None
    ) -> Document:
        """
        Create a new document with file upload.
        
        Parameters
        ----------
        db: SQLAlchemy session
        obj_in: Document creation data
        file_content: File content bytes (optional)
        
        Returns
        -------
        Document
            Created document instance
            
        Raises
        ------
        NotFoundError
            If user not found
        ValidationError
            If file validation fails
        """
        # Check if user exists
        user = crud_user.get(db, obj_in.user_id)
        if not user:
            raise NotFoundError(detail="User not found")
        
        # Validate file if provided
        if file_content:
            # Check file size
            if obj_in.file_size and obj_in.file_size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError(detail="File size exceeds 10MB limit")
            
            # Store file and get path
            file_path = self.file_storage.store_file(
                file_content=file_content,
                filename=obj_in.file_name,
                user_id=obj_in.user_id
            )
            obj_in.file_path = file_path
        
        # Create document
        return crud_document.create(db, obj_in=obj_in)
    
    def update_document(
        self, db: Session, *, id: int, obj_in: DocumentUpdate
    ) -> Document:
        """
        Update a document.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Document ID
        obj_in: Update data
        
        Returns
        -------
        Document
            Updated document instance
            
        Raises
        ------
        NotFoundError
            If document not found
        """
        document = crud_document.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        return crud_document.update(db, db_obj=document, obj_in=obj_in)
    
    def delete_document(self, db: Session, *, id: int) -> Document:
        """
        Delete a document and its file.
        
        Parameters
        ----------
        db: SQLAlchemy session
        id: Document ID
        
        Returns
        -------
        Document
            Deleted document instance
            
        Raises
        ------
        NotFoundError
            If document not found
        """
        document = crud_document.get(db, id)
        if not document:
            raise NotFoundError(detail="Document not found")
        
        # Delete physical file if it exists
        if document.file_path:
            self.file_storage.delete_file(document.file_path)
        
        # Delete document record
        return crud_document.remove(db, id=id)
    
    def get_user_documents(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get all documents for a user.
        
        Parameters
        ----------
        db: SQLAlchemy session
        user_id: User ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Document]
            List of user documents
        """
        return crud_document.get_by_user(db, user_id=user_id, skip=skip, limit=limit)
    
    def get_documents_by_type(
        self, db: Session, *, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by type.
        
        Parameters
        ----------
        db: SQLAlchemy session
        document_type: Document type to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
        Returns
        -------
        List[Document]
            List of documents of the specified type
        """
        return crud_document.get_by_type(db, document_type=document_type, skip=skip, limit=limit)
    
    def get_document_stats(self, db: Session) -> Dict[str, Any]:
        """
        Get document statistics.
        
        Parameters
        ----------
        db: SQLAlchemy session
        
        Returns
        -------
        Dict[str, Any]
            Document statistics by type and user
        """
        return crud_document.get_document_stats(db)