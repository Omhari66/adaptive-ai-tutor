"""
Chat endpoint with RAG capabilities
Supports both JSON response and SSE streaming
"""
import uuid
import json
from typing import List, Optional, AsyncGenerator, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document, DocumentStatus
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    documentIds: Optional[List[str]] = None
    sessionId: Optional[str] = None
    mode: str = "NORMAL"
    metadata: Optional[Dict[str, Any]] = None


class Source(BaseModel):
    page: int
    docId: str
    docName: str


class ChatResponse(BaseModel):
    message: str
    sources: List[Source]
    sessionId: str
    suggest_mode: Optional[str] = None
    confidence_score: Optional[float] = None


async def sse_generator(rag_service: RAGService, query: str, documents: List,
                        conversation_history: List[Dict], session_id: str, db: Session, user_id: str, mode: str) -> AsyncGenerator[str, None]:
    """
    SSE generator that streams RAG response tokens to the client.
    Also saves the complete message to the database after streaming completes.
    """
    full_response = ""
    sources = []

    # Emit session ID first so frontend can sync URL immediately
    yield f"data: {json.dumps({'type': 'session', 'sessionId': session_id})}\n\n"

    async for event in rag_service.generate_response_stream(
        query=query,
        documents=documents,
        conversation_history=conversation_history,
        mode=mode,
        user_id=user_id,
        db=db
    ):
        event_type = event.get("type")

        if event_type == "sources":
            sources = event.get("sources", [])
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        elif event_type in ["topic", "suggest_mode", "confidence_score"]:
            yield f"data: {json.dumps(event)}\n\n"

        elif event_type == "text":
            full_response += event.get("content", "")
            yield f"data: {json.dumps({'type': 'text', 'content': event.get('content')})}\n\n"

        elif event_type == "done":
            # Streaming complete - save to database
            user_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="user",
                content=query
            )
            db.add(user_message)

            assistant_message = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                role="assistant",
                content=full_response,
                sources=json.dumps(sources) if sources else None
            )
            db.add(assistant_message)
            db.commit()

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            break

    # End of SSE stream
    yield "data: [DONE]\n\n"


@router.post("")
async def chat(
    request: ChatRequest,
    request_obj: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Chat endpoint with RAG (Retrieval-Augmented Generation).
    Streams responses using Server-Sent Events (SSE) for real-time token streaming.

    Check Accept header to determine response format:
    - text/event-stream: Stream tokens via SSE
    - application/json: Return complete response (fallback)
    """
    # Get or create chat session
    session_id = request.sessionId
    if not session_id:
        session_id = str(uuid.uuid4())
        session = ChatSession(
            id=session_id,
            user_id=current_user.id,
            title=request.query[:50] + "..." if len(request.query) > 50 else request.query,
            mode=request.mode
        )
        db.add(session)
        db.commit()
    else:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # Update session mode if changed
        if session.mode != request.mode:
            session.mode = request.mode
            db.commit()

    # Get documents to search
    if request.documentIds:
        documents = db.query(Document).filter(
            Document.id.in_(request.documentIds),
            Document.user_id == current_user.id,
            Document.status == DocumentStatus.READY
        ).all()
    else:
        # Get all ready documents for user
        documents = db.query(Document).filter(
            Document.user_id == current_user.id,
            Document.status == DocumentStatus.READY
        ).all()

    # Get conversation history for query rewriting
    recent_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.desc()).limit(5).all()
    recent_messages = list(reversed(recent_messages))  # Oldest first

    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in recent_messages
    ]

    # Check if client wants SSE streaming
    accept_header = request_obj.headers.get("accept", "")

    if "text/event-stream" in accept_header:
        # SSE streaming response
        rag_service = RAGService()
        return StreamingResponse(
            sse_generator(rag_service, request.query, documents, conversation_history, session_id, db, current_user.id, request.mode),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Fallback to JSON response for backward compatibility
        rag_service = RAGService()

        if not documents:
            response_text = await rag_service.generate_without_context(request.query)
            return {
                "message": response_text,
                "sources": [],
                "sessionId": session_id
            }

        result = await rag_service.generate_response(
            query=request.query,
            documents=documents,
            conversation_history=conversation_history,
            mode=request.mode,
            user_id=current_user.id,
            db=db
        )

        # Save user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=request.query
        )
        db.add(user_message)

        # Save assistant message
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=result["text"],
            sources=json.dumps(result["sources"]) if result["sources"] else None
        )
        db.add(assistant_message)
        db.commit()

        # Format sources for response
        sources = []
        for src in result.get("sources", []):
            sources.append({
                "page": src.get("page", 0),
                "docId": src.get("docId", ""),
                "docName": src.get("docName", "")
            })

        return {
            "message": result["text"],
            "sources": sources,
            "sessionId": session_id,
            "suggest_mode": result.get("suggest_mode"),
            "confidence_score": result.get("confidence_score")
        }


@router.get("/sessions")
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all chat sessions for the current user"""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(ChatSession.updated_at.desc()).all()

    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title or "Untitled",
                "time": s.updated_at.strftime("%b %d") if s.updated_at else "Now",
                "is_pinned": s.is_pinned or False
            }
            for s in sessions
        ]
    }


@router.get("/{session_id}/messages")
async def get_chat_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all messages for a specific chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()

    formatted_messages = []
    for msg in messages:
        sources = []
        if msg.sources:
            try:
                sources = json.loads(msg.sources)
            except Exception:
                pass
        
        formatted_messages.append({
            "id": msg.id,
            "role": "ai" if msg.role == "assistant" else "user",
            "content": msg.content,
            "sources": sources
        })

    return {"messages": formatted_messages}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()

    return {"status": "deleted", "sessionId": session_id}


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None

@router.patch("/sessions/{session_id}")
async def update_chat_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session (rename or pin)"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update_data.title is not None:
        session.title = update_data.title
    if update_data.is_pinned is not None:
        session.is_pinned = update_data.is_pinned

    db.commit()

    return {
        "status": "updated", 
        "session": {
            "id": session.id,
            "title": session.title,
            "is_pinned": session.is_pinned
        }
    }
