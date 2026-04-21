"""
Quiz generation and management endpoints
"""
import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.quiz import Quiz, QuizQuestion, QuizResult
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizQuestionModel(BaseModel):
    id: str
    question: str
    options: List[str]
    correctAnswer: int
    explanation: str = ""


class QuizGenerateRequest(BaseModel):
    documentIds: Optional[List[str]] = None
    numQuestions: int = 5


class QuizGenerateResponse(BaseModel):
    quizId: str
    title: str
    questions: List[QuizQuestionModel]


class QuizSubmitRequest(BaseModel):
    quizId: str
    answers: List[int]  # Selected option index for each question


class QuizSubmitResponse(BaseModel):
    correctCount: int
    incorrectCount: int
    accuracy: float
    totalQuestions: int


@router.post("/generate")
async def generate_quiz(
    request: QuizGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a quiz based on uploaded documents.
    Uses LLM to create questions from document content.
    """
    try:
        # Get documents
        if request.documentIds:
            documents = db.query(Document).filter(
                Document.id.in_(request.documentIds),
                Document.status == DocumentStatus.READY,
                Document.user_id == current_user.id
            ).all()
            
            # Verify we found all requested documents (optional, but good practice)
            if len(documents) != len(request.documentIds):
                raise HTTPException(status_code=403, detail="Not authorized to access one or more of these documents, or they don't exist")
        else:
            documents = db.query(Document).filter(
                Document.status == DocumentStatus.READY,
                Document.user_id == current_user.id
            ).all()

        if not documents:
            raise HTTPException(status_code=400, detail="No documents available for quiz generation")

        # Generate quiz using LLM
        quiz_service = QuizService()
        quiz_data = await quiz_service.generate_quiz(documents, request.numQuestions)

        # Create quiz record
        quiz_id = str(uuid.uuid4())
        quiz = Quiz(
            id=quiz_id,
            user_id=current_user.id,
            title=quiz_data.get("title", "Study Quiz"),
            document_ids=json.dumps([doc.id for doc in documents]),
            total_questions=len(quiz_data.get("questions", []))
        )
        db.add(quiz)

        # Create questions
        for q_data in quiz_data.get("questions", []):
            question = QuizQuestion(
                id=str(uuid.uuid4()),
                quiz_id=quiz_id,
                question_text=q_data["question"],
                options=json.dumps(q_data["options"]),
                correct_answer=q_data["correctAnswer"],
                explanation=q_data.get("explanation", "")
            )
            db.add(question)

        db.commit()

        # Format response with explanations
        questions = []
        for q in quiz.questions:
            questions.append({
                "id": q.id,
                "question": q.question_text,
                "options": json.loads(q.options),
                "correctAnswer": q.correct_answer,
                "explanation": q.explanation or ""
            })

        return {
            "quizId": quiz_id,
            "title": quiz.title,
            "questions": questions
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import logging
        logging.getLogger(__name__).error(f"Quiz generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit quiz answers and get results.
    """
    quiz = db.query(Quiz).filter(Quiz.id == request.quizId, Quiz.user_id == current_user.id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    # Get questions
    questions = db.query(QuizQuestion).filter(
        QuizQuestion.quiz_id == request.quizId
    ).order_by(QuizQuestion.created_at).all()

    if len(questions) != len(request.answers):
        raise HTTPException(status_code=400, detail="Number of answers doesn't match questions")

    # Calculate score
    correct_count = 0
    incorrect_count = 0
    answer_details = []

    for i, question in enumerate(questions):
        selected = request.answers[i]
        is_correct = selected == question.correct_answer
        if is_correct:
            correct_count += 1
        else:
            incorrect_count += 1
        answer_details.append({
            "question_id": question.id,
            "selected": selected,
            "correct": question.correct_answer,
            "is_correct": is_correct
        })

    accuracy = (correct_count / len(questions)) * 100 if questions else 0

    # Save result
    result_id = str(uuid.uuid4())
    result = QuizResult(
        id=result_id,
        quiz_id=request.quizId,
        user_id=current_user.id,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        accuracy=accuracy,
        answers=json.dumps(answer_details)
    )
    db.add(result)
    db.commit()

    return {
        "correctCount": correct_count,
        "incorrectCount": incorrect_count,
        "accuracy": accuracy,
        "totalQuestions": len(questions)
    }


@router.get("/history")
async def get_quiz_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quiz results for the current user"""
    results = db.query(QuizResult).filter(
        QuizResult.user_id == current_user.id
    ).order_by(QuizResult.completed_at.desc()).all()

    return {
        "results": [
            {
                "id": r.id,
                "quizId": r.quiz_id,
                "accuracy": r.accuracy,
                "correctCount": r.correct_count,
                "totalQuestions": r.correct_count + r.incorrect_count,
                "completedAt": r.completed_at.strftime("%Y-%m-%d %H:%M") if r.completed_at else "Unknown"
            }
            for r in results
        ]
    }
