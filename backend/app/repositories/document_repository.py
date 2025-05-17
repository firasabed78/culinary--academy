"""
Objective: Implement a specialized repository for document operations.
This file extends the base repository with document-specific query methods,
providing advanced filtering and retrieval capabilities for document records.

The DocumentRepository continues the pattern of extending the base repository with domain-specific query methods, this time focusing on document management requirements.
Key Features:

Document-Specific Queries:

User-Based Filtering: Retrieve documents by owner
Type Classification: Filter by document type (enum-based)
File Format Filtering: Search by file extension
Multi-Criteria Search: Combine user and document type filters


Data Access Patterns:

Eager Loading: Optimize related data loading with joinedload
Pagination Support: Consistent skip and limit parameters across methods
Query Filtering: Clean filter application based on provided parameters
Text Search: Case-insensitive file name and description searching


Design Considerations:

Specialization: Methods tailored to document management use cases
Reuse: Leveraging base repository for standard CRUD operations
Consistency: Following the repository pattern established in other parts of the application
Encapsulation: Complex SQL logic hidden behind simple method interfaces


Notable Implementation Details:

Document Type Support: Using the DocumentType enum for type-safe filtering
Textual Search: Supporting search across both file name and description
Combined Filtering: Methods that apply multiple filter criteria simultaneously
Related Entity Loading: Efficiently retrieving document owners



This repository effectively manages the document storage component of your culinary academy application, providing a clean API for storing and retrieving various types of documents (such as student submissions, course materials, certificates, etc.) while maintaining appropriate access controls through user-based filtering.
The implementation shows a good balance of simplicity and functionality, with methods that closely match the typical use cases for document management in an educational context.

"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload  # For eager loading relationships
from app.domain.models.document import Document, DocumentType
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.repositories.base import BaseRepository

class DocumentRepository(BaseRepository[Document, DocumentCreate, DocumentUpdate]):
    """
    Repository for document operations.
    
    Extends the base repository with document-specific queries for
    retrieving and filtering document records based on various criteria.
    """
    
    def __init__(self):
        """Initialize with Document model."""
        super().__init__(Document)
    
    def get_with_user(self, db: Session, id: int) -> Optional[Document]:
        """
        Get a document with related user data.
        
        Uses eager loading to retrieve a document with its associated user
        in a single query, improving performance for detailed views.
        
        Args:
            db: SQLAlchemy database session
            id: Document ID
            
        Returns:
            Document with loaded user relationship or None if not found
        """
        return db.query(self.model)\
            .options(joinedload(self.model.user))\
            .filter(self.model.id == id)\
            .first()
    
    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get all documents for a user.
        
        Retrieves all documents owned by a specific user with pagination.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents owned by the specified user
        """
        return db.query(self.model)\
            .filter(self.model.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_document_type(
        self, db: Session, *, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by type.
        
        Retrieves documents of a specific document type with pagination.
        
        Args:
            db: SQLAlchemy database session
            document_type: DocumentType enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents of the specified type
        """
        return db.query(self.model)\
            .filter(self.model.document_type == document_type)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_file_type(
        self, db: Session, *, file_type: str, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by file type.
        
        Retrieves documents with a specific file type (e.g., 'pdf', 'docx')
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            file_type: File type extension to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents with the specified file type
        """
        return db.query(self.model)\
            .filter(self.model.file_type == file_type)\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_by_user_and_document_type(
        self, db: Session, *, user_id: int, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """
        Get documents by user and document type.
        
        Retrieves documents that match both a specific user and document type
        with pagination.
        
        Args:
            db: SQLAlchemy database session
            user_id: User ID to filter by
            document_type: DocumentType enum value to filter by
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of documents matching both user and document type
        """
        return db.query(self.model)\
            .filter(
                self.model.user_id == user_id,
                self.model.document_type == document_type
            )\
            .offset(skip)\
            .limit(limit)\
            .all()
    
    def get_multi_by_filters(
        self, db: Session, *, skip: int = 0, limit: int = 100, **filters
    ) -> List[Document]:
        """
        Get documents with complex filtering.
        
        Applies multiple filtering conditions based on the provided
        filter parameters, supporting a wide range of query criteria.
        
        Args:
            db: SQLAlchemy database session
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Field name/value pairs for filtering
            
        Returns:
            List of documents matching the filter criteria
        """
        query = db.query(self.model)
        
        # Apply filters based on filter name and value
        for key, value in filters.items():
            if key == "user_id" and value:
                query = query.filter(self.model.user_id == value)
            elif key == "document_type" and value:
                query = query.filter(self.model.document_type == value)
            elif key == "file_type" and value:
                query = query.filter(self.model.file_type == value)
            elif key == "search" and value:
                # Search in filename and description
                search_term = f"%{value}%"
                query = query.filter(
                    self.model.file_name.ilike(search_term) |
                    self.model.description.ilike(search_term)
                )
        
        return query.offset(skip).limit(limit).all()