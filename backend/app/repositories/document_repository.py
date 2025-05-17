from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.domain.models.document import Document, DocumentType
from app.domain.schemas.document import DocumentCreate, DocumentUpdate
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document, DocumentCreate, DocumentUpdate]):
    """Repository for document operations."""
    
    def __init__(self):
        super().__init__(Document)

    def get_with_user(self, db: Session, id: int) -> Optional[Document]:
        """Get a document with related user data."""
        return db.query(self.model)\
            .options(joinedload(self.model.user))\
            .filter(self.model.id == id)\
            .first()

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get all documents for a user."""
        return db.query(self.model)\
            .filter(self.model.user_id == user_id)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_document_type(
        self, db: Session, *, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get documents by type."""
        return db.query(self.model)\
            .filter(self.model.document_type == document_type)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_file_type(
        self, db: Session, *, file_type: str, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get documents by file type."""
        return db.query(self.model)\
            .filter(self.model.file_type == file_type)\
            .offset(skip)\
            .limit(limit)\
            .all()

    def get_by_user_and_document_type(
        self, db: Session, *, user_id: int, document_type: DocumentType, skip: int = 0, limit: int = 100
    ) -> List[Document]:
        """Get documents by user and document type."""
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
        """Get documents with complex filtering."""
        query = db.query(self.model)
        
        for key, value in filters.items():
            if key == "user_id" and value:
                query = query.filter(self.model.user_id == value)
            elif key == "document_type" and value:
                query = query.filter(self.model.document_type == value)
            elif key == "file_type" and value:
                query = query.filter(self.model.file_type == value)
            elif key == "search" and value:
                search_term = f"%{value}%"
                query = query.filter(
                    self.model.file_name.ilike(search_term) | 
                    self.model.description.ilike(search_term)
                )
        
        return query.offset(skip).limit(limit).all()