from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.api import deps
from app.domain.models.user import User
from app.domain.models.document import DocumentType
from app.domain.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentWithUser
)
from app.services.document_service import DocumentService
from app.core.exceptions import NotFoundError, ValidationError

router = APIRouter()
document_service = DocumentService()

@router.get("/", response_model=List[Document])
def read_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    document_type: Optional[DocumentType] = None,
    search: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve documents with filtering.
    """
    # Build filters
    filters = {}
    if document_type:
        filters["document_type"] = document_type
    if search:
        filters["search"] = search
    
    # Apply access control based on user role
    if current_user.role == "admin":
        # Admins can view anyone's documents
        if user_id:
            filters["user_id"] = user_id
    else:
        # Regular users can only view their own documents
        filters["user_id"] = current_user.id
        if user_id and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access other users' documents"
            )
    
    return document_service.get_filtered_documents(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=Document)
async def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    document_type: DocumentType,
    description: Optional[str] = None,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Upload a new document.
    """
    try:
        return await document_service.upload_document(
            db, 
            file=file, 
            document_type=document_type,
            user_id=current_user.id,
            description=description
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=DocumentWithUser)
def read_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get document by ID with user details.
    """
    try:
        document = document_service.get_with_user(db, id)
        
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        return document
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.get("/{id}/download")
def download_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Download document file.
    """
    try:
        document = document_service.get(db, id)
        
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this document"
            )
        
        # Get file info
        file_info = document_service.get_document_file(db, id=id)
        
        # Return file
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["file_name"],
            media_type=f"application/{file_info['file_type']}"
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/{id}", response_model=Document)
def update_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    document_in: DocumentUpdate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update document metadata.
    """
    try:
        document = document_service.get(db, id)
        
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this document"
            )
        
        return document_service.update(db, id=id, obj_in=document_in)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{id}", response_model=Document)
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete document and its file.
    """
    try:
        document = document_service.get(db, id)
        
        # Check permissions
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document"
            )
        
        return document_service.delete_document(db, id=id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )