"""
Chat models for storing conversation history
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    """Chat session table for grouping related messages"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # Made nullable for default user
    title = Column(String, nullable=True)  # Auto-generated from first message
    mode = Column(String, default="NORMAL", server_default="NORMAL")  # Active mode
    topic = Column(String, nullable=True)  # Active topic
    is_pinned = Column(Boolean, default=False, server_default="0") # Added pinned column
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, title={self.title}, mode={self.mode})>"


class ChatMessage(Base):
    """Individual chat messages within a session"""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)  # UUID
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)

    # RAG-specific fields
    query_embedding_id = Column(String, nullable=True)  # Qdrant point ID for the query
    retrieved_chunk_ids = Column(Text, nullable=True)  # JSON array of chunk IDs used

    # Sources/citations
    sources = Column(Text, nullable=True)  # JSON array of source references

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session={self.session_id})>"
