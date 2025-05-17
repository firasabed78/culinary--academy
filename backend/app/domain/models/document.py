from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class DocumentType(str, enum.Enum):
    ID_PROOF = "id_proof"
    CERTIFICATION = "certification"
    RESUME = "resume"
    TRANSCRIPT = "transcript"
    OTHER = "other"

class Document(Base):
    """User document uploads."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=True)  # mime type or extension
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    document_type = Column(Enum(DocumentType), nullable=False)
    description = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    
    # Relationships
    user = relationship("User", back_populates="documents")
    
    class Config:
        orm_mode = True