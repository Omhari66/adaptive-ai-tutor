import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.models.learning_state import LearningState

logger = logging.getLogger(__name__)

class LearningStateService:
    """
    Manages user learning state, applying confidence tuning and adaptive mode triggering.
    """
    
    def __init__(self):
        self.CONFIDENCE_INCREMENT = 0.1
        self.CONFIDENCE_DECREMENT = 0.15
        self.MIN_CONFIDENCE = 0.0
        self.MAX_CONFIDENCE = 1.0
        self.WEAKNESS_THRESHOLD = 0.4

    def update_confidence(self, db: Session, user_id: str, topic: str, is_correct: bool) -> float:
        """
        Updates the user's confidence score for a topic.
        Returns the new confidence score.
        """
        if not user_id or topic == "general":
            return 0.5  # Neutral for general or anonymous

        state = db.query(LearningState).filter(
            LearningState.user_id == user_id,
            LearningState.topic_name == topic
        ).first()

        if not state:
            state = LearningState(
                id=str(uuid.uuid4()),
                user_id=user_id,
                topic_name=topic,
                confidence_score=0.5,
                mistakes_count=0
            )
            db.add(state)

        # Apply score changes with decay filter
        state.confidence_score *= 0.95

        if is_correct:
            state.confidence_score += self.CONFIDENCE_INCREMENT
        else:
            state.confidence_score -= self.CONFIDENCE_DECREMENT
            state.mistakes_count += 1

        # Cap the values
        state.confidence_score = max(self.MIN_CONFIDENCE, min(self.MAX_CONFIDENCE, state.confidence_score))

        db.commit()
        db.refresh(state)

        logger.info(f"LearningState: {user_id} on {topic} -> confidence {state.confidence_score:.2f}")
        return state.confidence_score

    def get_suggested_mode(self, db: Session, user_id: str, topic: str, same_question_count: int = 0) -> str:
        """
        Calculates if the system should trigger an adaptive mode switch.
        """
        if not user_id or topic == "general":
            return "PRACTICE"

        state = db.query(LearningState).filter(
            LearningState.user_id == user_id,
            LearningState.topic_name == topic
        ).first()

        if not state:
            return "PRACTICE"

        if state.confidence_score < 0.4:
            return "REVISION"
        elif state.confidence_score > 0.7:
            return "EXAM"
        else:
            return "PRACTICE"

    def get_weak_topics(self, db: Session, user_id: str, limit: int = 3) -> list[str]:
        """
        Retrieves the weakest topics for a user
        """
        if not user_id: return []
        states = db.query(LearningState).filter(
            LearningState.user_id == user_id
        ).order_by(LearningState.confidence_score.asc()).limit(limit).all()
        return [s.topic_name for s in states]

def get_learning_state_service() -> LearningStateService:
    return LearningStateService()
