"""
Quiz models for storing quiz data and results
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Quiz(Base):
    """Quiz table for storing generated quizzes"""
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    document_ids = Column(Text, nullable=True)  # JSON array of document IDs used
    total_questions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    results = relationship("QuizResult", back_populates="quiz", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Quiz(id={self.id}, title={self.title})>"


class QuizQuestion(Base):
    """Individual questions within a quiz"""
    __tablename__ = "quiz_questions"

    id = Column(String, primary_key=True)  # UUID
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON array of options
    correct_answer = Column(Integer, nullable=False)  # Index of correct option
    explanation = Column(Text, nullable=True)
    source_chunk_id = Column(String, nullable=True)  # Reference to document chunk
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")

    def __repr__(self):
        return f"<QuizQuestion(id={self.id}, quiz={self.quiz_id})>"


class QuizResult(Base):
    """Quiz results for tracking user performance"""
    __tablename__ = "quiz_results"

    id = Column(String, primary_key=True)  # UUID
    quiz_id = Column(String, ForeignKey("quizzes.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Score tracking
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)  # Percentage 0-100

    # Detailed answers
    answers = Column(Text, nullable=True)  # JSON array of {question_id, selected_index, is_correct}

    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    quiz = relationship("Quiz", back_populates="results")
    user = relationship("User")

    def __repr__(self):
        return f"<QuizResult(id={self.id}, quiz={self.quiz_id}, accuracy={self.accuracy})>"
