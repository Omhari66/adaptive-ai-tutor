"""
Document management endpoints
"""
import uuid
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.worker import process_document_task
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str
    size: str
    status: str
    pages: int
    dateAdded: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user)
):
    """
    Upload a document for processing.
    Returns immediately with a document ID while background processing occurs.
    Uses PyMuPDF for PDF parsing and FastAPI BackgroundTasks for async processing.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]

    # Handle edge case where content_type might be None
    content_type = file.content_type or ""
    if content_type not in allowed_types:
        # Also check by extension as fallback
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in ["pdf", "docx", "txt"]:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX, and TXT files are allowed"
            )

    # Generate document ID
    doc_id = str(uuid.uuid4())

    # Determine file extension
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
    file_type = "pdf" if ext == "pdf" else "docx" if ext == "docx" else "txt"

    # Read file content
    file_content = await file.read()

    # Validate file size
    max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Create database record
    document = Document(
        id=doc_id,
        user_id=current_user.id,
        name=file.filename or "Untitled",
        file_path=f"uploads/{doc_id}.{ext}",
        file_type=file_type,
        file_size=len(file_content),  # Set actual size
        status=DocumentStatus.PENDING,
    )
    # Save file immediately before queueing
    file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}.{ext}")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file_content)

    document.file_path = file_path
    db.add(document)
    db.commit()

    # Schedule background processing immediately natively
    # This prevents the long connection timeout when Redis isn't running locally!
    from app.services.document_service import process_document_async
    background_tasks.add_task(process_document_async, doc_id, file_content)

    return {
        "status": "processing",
        "docId": doc_id
    }


@router.get("")
async def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all documents for the current user.
    """
    # Get all documents for the current user.
    documents = db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()

    result = []
    for doc in documents:
        # Convert bytes to human readable
        size_bytes = doc.file_size or 0
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        # Calculate relative time
        from datetime import datetime
        now = datetime.now()
        diff = now - doc.created_at
        if diff.total_seconds() < 3600:
            time_str = f"{int(diff.total_seconds() / 60)} minutes ago"
        elif diff.total_seconds() < 86400:
            time_str = f"{int(diff.total_seconds() / 3600)} hours ago"
        else:
            time_str = f"{int(diff.total_seconds() / 86400)} days ago"

        result.append({
            "id": doc.id,
            "name": doc.name,
            "type": doc.file_type,
            "size": size_str,
            "status": doc.status.value,
            "pages": doc.page_count or 0,
            "dateAdded": time_str
        })

    return {"documents": result}


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a document and its associated chunks.
    """
    document = db.query(Document).filter(Document.id == doc_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()

    logger.info(f"Document deleted: {doc_id}")
    return {"status": "deleted", "docId": doc_id}
