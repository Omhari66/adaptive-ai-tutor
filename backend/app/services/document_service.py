"""
Document processing service
Handles PDF/DOCX parsing, chunking, and vector embedding generation
"""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for document parsing, chunking, and embedding.
    """

    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self._embedding_service = None
        os.makedirs(self.upload_dir, exist_ok=True)

    def _get_embedding_service(self):
        """Lazy load embedding service singleton"""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    def _parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse PDF file and extract text by page.
        Uses PyMuPDF for structure-aware parsing.
        """
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(file_path)
            pages = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                # Try to preserve table structure
                tables = page.find_tables()
                if tables:
                    # Extract tables separately for better structure
                    for table in tables:
                        table_text = table.extract()
                        # Format table as markdown-like structure
                        formatted_table = "\n".join(
                            " | ".join(str(cell) if cell else "" for cell in row)
                            for row in table_text
                        )
                        text += f"\n\n[Table]\n{formatted_table}\n[/Table]\n"

                pages.append({
                    "page_number": page_num + 1,
                    "content": text.strip()
                })

            doc.close()
            return pages

        except ImportError:
            raise RuntimeError("PyMuPDF not installed. Install with: pip install PyMuPDF")
        except Exception as e:
            raise RuntimeError(f"Error parsing PDF: {e}")

    def _parse_docx(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse DOCX file and extract text.
        """
        try:
            from docx import Document

            doc = Document(file_path)
            pages = []
            current_content = []
            page_num = 1

            for para in doc.paragraphs:
                if para.text.strip():
                    current_content.append(para.text)

                # Simple page break detection (approximate)
                if len(current_content) > 5000:  # Rough page boundary
                    pages.append({
                        "page_number": page_num,
                        "content": "\n".join(current_content).strip()
                    })
                    current_content = []
                    page_num += 1

            if current_content:
                pages.append({
                    "page_number": page_num,
                    "content": "\n".join(current_content).strip()
                })

            return pages

        except ImportError:
            raise RuntimeError("python-docx not installed. Install with: pip install python-docx")
        except Exception as e:
            raise RuntimeError(f"Error parsing DOCX: {e}")

    def _parse_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse plain text file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into approximate pages (3000 chars per page)
            pages = []
            page_size = 3000
            page_num = 1

            for i in range(0, len(content), page_size):
                chunk = content[i:i + page_size]
                pages.append({
                    "page_number": page_num,
                    "content": chunk.strip()
                })
                page_num += 1

            return pages

        except Exception as e:
            raise RuntimeError(f"Error parsing TXT: {e}")

    def _chunk_content(
        self,
        content: str,
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[str]:
        """
        Split content into overlapping chunks for better retrieval.
        Preserves sentence boundaries where possible.
        """
        chunks = []
        start = 0

        while start < len(content):
            end = start + chunk_size

            # Try to end at sentence boundary
            if end < len(content):
                # Look for sentence end within 50 chars of chunk end
                search_range = content[end - 50:end + 50] if end > 50 else content[:end + 50]
                for punct in ['.', '!', '?', '\n']:
                    last_idx = search_range.rfind(punct)
                    if last_idx != -1:
                        if end > 50:
                            end = (end - 50) + last_idx + 1
                        else:
                            end = last_idx + 1
                        break

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap

        return chunks

    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using shared embedding service"""
        embedding_service = self._get_embedding_service()
        return embedding_service.generate_embedding(text)

    async def _store_in_vector_db(
        self,
        chunk_id: str,
        content: str,
        document_id: str,
        document_name: str,
        page_number: int,
        embedding: List[float]
    ):
        """
        Store chunk embedding in Qdrant vector database.
        """
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import PointStruct, VectorParams, Distance

            if settings.QDRANT_URL == "local":
                client = QdrantClient(path="./qdrant_data")
            else:
                client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY
                )

            # Ensure collection exists using the recommended idiom
            collection = settings.QDRANT_COLLECTION_NAME
            if not client.collection_exists(collection_name=collection):
                client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(
                        size=384,  # Size for all-MiniLM-L6-v2
                        distance=Distance.COSINE
                    )
                )

            # Upsert point
            client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=chunk_id,
                        vector=embedding,
                        payload={
                            "content": content,
                            "document_id": document_id,
                            "document_name": document_name,
                            "page_number": page_number
                        }
                    )
                ]
            )

        except ImportError as e:
            logger.error(f"Qdrant client not installed. Skipping vector storage: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error storing in vector DB: {e}")
            raise e

    async def process_document(
        self,
        document_id: str,
        db: Optional[Session] = None
    ):
        """
        Process a document: parse, chunk, embed, and store.
        """
        # Get document from database
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            db.commit()

            # Parse document based on type
            file_path = os.path.join(self.upload_dir, os.path.basename(document.file_path))

            if document.file_type == "pdf":
                pages = self._parse_pdf(file_path)
            elif document.file_type == "docx":
                pages = self._parse_docx(file_path)
            else:
                pages = self._parse_txt(file_path)

            # Update page count
            document.page_count = len(pages)
            document.file_size = os.path.getsize(file_path)
            db.commit()

            # Process each page
            chunk_index = 0
            for page in pages:
                # Chunk the page content
                chunks = self._chunk_content(
                    page["content"],
                    chunk_size=settings.CHUNK_SIZE,
                    overlap=settings.CHUNK_OVERLAP
                )

                for chunk_text in chunks:
                    # Generate embedding
                    embedding = await self._generate_embedding(chunk_text)

                    # Create chunk record
                    chunk_id = str(uuid.uuid4())
                    chunk = DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        content=chunk_text,
                        page_number=page["page_number"],
                        chunk_index=chunk_index,
                        token_count=len(chunk_text) // 4,  # Approximate
                        embedding_id=chunk_id
                    )
                    db.add(chunk)
                    chunk_index += 1

                    # Store in vector database
                    await self._store_in_vector_db(
                        chunk_id=chunk_id,
                        content=chunk_text,
                        document_id=document_id,
                        document_name=document.name,
                        page_number=page["page_number"],
                        embedding=embedding
                    )

            # Mark document as ready
            document.status = DocumentStatus.READY
            db.commit()

        except Exception as e:
            # Mark as failed
            if 'document' in locals():
                document.status = DocumentStatus.FAILED
                db.commit()
            raise e
        finally:
            if should_close:
                db.close()


async def process_document_async(document_id: str, file_content: bytes):
    """
    Background task wrapper for document processing.
    Saves file and triggers processing pipeline.
    """
    service = DocumentService()

    # Save file
    doc = None
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            # file is already saved before task execution, we just execute process_document
            await service.process_document(document_id, db)

    except Exception as e:
        logger.error(f"Document processing error: {e}")
        if doc:
            doc.status = DocumentStatus.FAILED
            db.commit()
    finally:
        db.close()
