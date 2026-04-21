from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class LearningState(Base):
    """
    Tracks the user's proficiency, confidence, and mistakes for specific topics.
    Used for adaptive tuning of the RAG responses and mode generation.
    """
    __tablename__ = "learning_states"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    topic_name = Column(String, nullable=False, index=True)
    
    # Confidence from 0.0 to 1.0
    confidence_score = Column(Float, default=0.5, nullable=False)
    
    # Absolute count of mistakes
    mistakes_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_interaction = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<LearningState(user={self.user_id}, topic={self.topic_name}, confidence={self.confidence_score})>"
