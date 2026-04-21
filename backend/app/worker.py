import os
from celery import Celery
from asgiref.sync import async_to_sync
from app.core.config import settings
from app.services.document_service import DocumentService
from app.core.database import SessionLocal
from app.models.document import Document, DocumentStatus
import logging

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "rag_assistant_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True
)

@celery_app.task(name="process_document_task")
def process_document_task(document_id: str):
    """
    Celery task that processes a document purely by looking up its saved file
    """
    logger.info(f"Starting Celery task to process document: {document_id}")
    db = SessionLocal()
    doc = None
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.error(f"Document {document_id} not found in database.")
            return

        service = DocumentService()
        
        # We must run the async method synchronously inside this Celery worker thread
        async_to_sync(service.process_document)(document_id, db)
        
        logger.info(f"Successfully processed document: {document_id}")
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        if doc:
            doc.status = DocumentStatus.FAILED
            db.commit()
    finally:
        db.close()
