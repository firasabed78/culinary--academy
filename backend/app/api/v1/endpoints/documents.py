"""
Objective: Implement document management endpoints.
This file defines the API endpoints for uploading, retrieving, updating, and
deleting documents, with proper access control and file handling.

This file implements a comprehensive document management API:

Purpose: Provides a complete CRUD interface for document management with file handling and access control.
Key Endpoints:

GET /: List documents with filtering and pagination
POST /: Upload new documents with metadata
GET /{id}: Retrieve a specific document's metadata
GET /{id}/download: Download the actual document file
PUT /{id}: Update document metadata
DELETE /{id}: Delete a document and its file


Design Patterns:

Role-based Access Control (RBAC): Different permissions for admins vs. regular users
Separation of Concerns: Routes handle HTTP logic, services handle business logic
File Handling: Proper file uploads and downloads with appropriate MIME types
Error Handling: Custom exceptions mapped to appropriate HTTP responses


Security Features:

Authentication for all endpoints
Authorization checks for each operation
Data isolation between users
Secure file handling


Notable Implementation Details:

Uses FastAPI's File handling for uploads
Uses FileResponse for file downloads
Implements filtering, pagination, and search
Differentiates between metadata operations vs. file operations



This endpoint demonstrates a mature approach to file management in a web API, properly separating concerns between HTTP handling, business logic, and data access, while maintaining strong security through consistent access control checks.

"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import FileResponse  # For file downloads
from sqlalchemy.orm import Session
import os

from app.api import deps  # Authentication dependencies
from app.domain.models.user import User
from app.domain.models.document import DocumentType  # Enum of document types
from app.domain.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentWithUser  # Data models/schemas
)
from app.services.document_service import DocumentService  # Document business logic
from app.core.exceptions import NotFoundError, ValidationError  # Custom exceptions

# Create a router for document endpoints
router = APIRouter()

# Create a service instance for document operations
document_service = DocumentService()

@router.get("/", response_model=List[Document])
def read_documents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,  # Pagination offset
    limit: int = 100,  # Pagination limit
    user_id: Optional[int] = None,  # Filter by user ID
    document_type: Optional[DocumentType] = None,  # Filter by document type
    search: Optional[str] = None,  # Search in document metadata
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Retrieve documents with filtering.
    
    This endpoint returns a list of documents with optional filtering by user,
    document type, and search term. Access control ensures users only see
    documents they're authorized to view.
    """
    # Build filters dictionary for the service layer
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
    
    # Get filtered documents from service
    return document_service.get_filtered_documents(
        db, skip=skip, limit=limit, **filters
    )

@router.post("/", response_model=Document)
async def upload_document(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),  # The uploaded file
    document_type: DocumentType,  # Document classification
    description: Optional[str] = None,  # Optional document description
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Upload a new document.
    
    This endpoint handles file uploads, stores the file, and creates a
    document record in the database linking the file to the user.
    """
    try:
        # Use document service to handle the upload
        return await document_service.upload_document(
            db, 
            file=file, 
            document_type=document_type,
            user_id=current_user.id,
            description=description
        )
    except ValidationError as e:
        # Handle validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/{id}", response_model=DocumentWithUser)
def read_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Document ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Get document by ID with user details.
    
    This endpoint returns a single document with its associated user's information,
    ensuring the requester has permission to view it.
    """
    try:
        # Get document with user details
        document = document_service.get_with_user(db, id)
        
        # Check permissions - only admins or the document owner can view
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )
        
        return document
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))

@router.get("/{id}/download")
def download_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Document ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Download document file.
    
    This endpoint streams the actual document file to the client,
    with proper content type and filename headers.
    """
    try:
        # Get document metadata
        document = document_service.get(db, id)
        
        # Check permissions - only admins or the document owner can download
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this document"
            )
        
        # Get file info including path
        file_info = document_service.get_document_file(db, id=id)
        
        # Return file as a downloadable response
        return FileResponse(
            path=file_info["file_path"],
            filename=file_info["file_name"],
            media_type=f"application/{file_info['file_type']}"
        )
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.put("/{id}", response_model=Document)
def update_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Document ID
    document_in: DocumentUpdate,  # Update data
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Update document metadata.
    
    This endpoint updates document information such as title, description,
    or document type, but does not replace the file itself.
    """
    try:
        # Get document to check permissions
        document = document_service.get(db, id)
        
        # Check permissions - only admins or the document owner can update
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this document"
            )
        
        # Update document
        return document_service.update(db, id=id, obj_in=document_in)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.delete("/{id}", response_model=Document)
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    id: int,  # Document ID
    current_user: User = Depends(deps.get_current_active_user),  # Authenticated user
) -> Any:
    """
    Delete document and its file.
    
    This endpoint removes both the document record from the database
    and the associated file from storage.
    """
    try:
        # Get document to check permissions
        document = document_service.get(db, id)
        
        # Check permissions - only admins or the document owner can delete
        if current_user.role != "admin" and document.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this document"
            )
        
        # Delete document and file
        return document_service.delete_document(db, id=id)
    except NotFoundError as e:
        # Handle not found errors
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e.detail))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )