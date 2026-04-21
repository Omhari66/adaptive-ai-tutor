"""
Progress and analytics endpoints
"""
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.quiz import QuizResult
from app.models.chat import ChatMessage, ChatSession

router = APIRouter(prefix="/progress", tags=["progress"])


class WeakTopic(BaseModel):
    topic: str
    score: float


class ProgressResponse(BaseModel):
    overallAccuracy: str
    quizzesCompleted: int
    conceptsMastered: int
    accuracy: List[float]
    weakTopics: List[WeakTopic]


@router.get("")
async def get_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user progress and analytics.
    Calculates accuracy trends and identifies weak topics.
    """
    user_id = current_user.id

    # Get all quiz results
    results = db.query(QuizResult).filter(
        QuizResult.user_id == user_id
    ).order_by(QuizResult.completed_at).all()

    # Calculate overall accuracy
    if results:
        total_correct = sum(r.correct_count for r in results)
        total_questions = sum(r.correct_count + r.incorrect_count for r in results)
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
    else:
        overall_accuracy = 0

    # Get accuracy trend (last 7 quizzes/weeks)
    accuracy_trend = []
    for result in results[-7:]:
        accuracy_trend.append(round(result.accuracy, 1))

    # Pad with zeros if less than 7 data points
    while len(accuracy_trend) < 7:
        accuracy_trend.insert(0, 0)

    # If no results, accuracy trend is purely zeroes
    if not accuracy_trend:
        accuracy_trend = [0] * 7

    # Identify weak topics from incorrect answers
    weak_topics = []

    # Get questions that were answered incorrectly
    incorrect_results = db.query(QuizResult).filter(
        QuizResult.user_id == user_id,
        QuizResult.accuracy < 80
    ).order_by(QuizResult.completed_at.desc()).limit(3).all()

    # In a full implementation, we'd extract specific topics. For now, empty or dynamically pulled from failed quiz titles if available.
    if incorrect_results:
        from app.models.quiz import Quiz
        for res in incorrect_results:
            quiz = db.query(Quiz).filter(Quiz.id == res.quiz_id).first()
            if quiz:
                weak_topics.append({"topic": quiz.title, "score": res.accuracy})

    # Count concepts mastered (based on high quiz scores)
    high_scores = db.query(QuizResult).filter(
        QuizResult.user_id == user_id,
        QuizResult.accuracy >= 90
    ).count()
    concepts_mastered = high_scores * 6  # Estimate: 6 concepts per high-score quiz

    # Format overall accuracy string
    if results:
        # Calculate week-over-week change
        if len(results) >= 2:
            accuracy_str = f"{round(overall_accuracy)}%"
        else:
            accuracy_str = f"{round(overall_accuracy)}%"
    else:
        accuracy_str = "0%"  # No results yet

    return {
        "overallAccuracy": accuracy_str,
        "quizzesCompleted": len(results),
        "conceptsMastered": concepts_mastered,
        "accuracy": accuracy_trend,
        "weakTopics": weak_topics
    }


@router.get("/recent-activity")
async def get_recent_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent chat and quiz activity"""
    user_id = current_user.id

    # Get recent chats
    recent_chats = db.query(ChatMessage).filter(
        ChatMessage.session_id.in_(
            db.query(ChatSession.id).filter(ChatSession.user_id == user_id)
        )
    ).order_by(ChatMessage.created_at.desc()).limit(10).all()

    # Get recent quiz results
    recent_quizzes = db.query(QuizResult).filter(
        QuizResult.user_id == user_id
    ).order_by(QuizResult.completed_at.desc()).limit(5).all()

    return {
        "chats": [
            {
                "id": msg.id,
                "preview": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                "time": msg.created_at.strftime("%b %d") if msg.created_at else "Now"
            }
            for msg in recent_chats
        ],
        "quizzes": [
            {
                "id": r.id,
                "accuracy": r.accuracy,
                "time": r.completed_at.strftime("%b %d") if r.completed_at else "Now"
            }
            for r in recent_quizzes
        ]
    }
