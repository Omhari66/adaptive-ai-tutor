"""
Quiz generation service
Creates active recall quizzes from document content
"""
import json
import logging
from typing import List, Dict, Any
from groq import AsyncGroq
from app.core.config import settings
from app.models.document import Document

logger = logging.getLogger(__name__)

class QuizService:
    """
    Service for generating quizzes from document content.
    Uses LLM to create questions based on document chunks.
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate_quiz(
        self,
        documents: List[Document],
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on document content.
        Returns quiz title and questions.
        """
        # Gather sample content from documents
        # In production, this would query the vector DB for diverse chunks
        sample_content = []

        try:
            from app.core.database import SessionLocal
            from app.models.document import DocumentChunk

            db = SessionLocal()
            for doc in documents:
                chunks = db.query(DocumentChunk).filter(
                    DocumentChunk.document_id == doc.id
                ).limit(3).all()

                for chunk in chunks:
                    sample_content.append({
                        "document_name": doc.name,
                        "content": chunk.content[:500]  # Limit content length
                    })

            db.close()
        except Exception as e:
            logger.error(f"Error fetching document chunks: {e}")
            # Fallback: use document names only
            for doc in documents:
                sample_content.append({
                    "document_name": doc.name,
                    "content": f"Document: {doc.name}"
                })

        if not sample_content:
            return {
                "title": "General Knowledge Quiz",
                "questions": []
            }

        # Build prompt for LLM
        content_str = "\n\n---\n\n".join([
            f"[From {item['document_name']}]\n{item['content']}"
            for item in sample_content
        ])

        prompt = f"""Based on the following study material, generate {num_questions} multiple-choice questions for active recall practice.

Study Material:
{content_str}

Generate questions that:
1. Test understanding of key concepts
2. Have exactly 4 options
3. Include only ONE correct answer
4. Cover diverse topics from the material
5. Are clear and unambiguous

Respond with a JSON object in this exact format:
{{
    "title": "Quiz Title Here",
    "questions": [
        {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correctAnswer": 0,
            "explanation": "Brief explanation of why this is correct"
        }}
    ]
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educator creating multiple-choice quiz questions. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )

        # Parse response
        try:
            response_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]

            quiz_data = json.loads(response_text)

            # Validate structure
            if "questions" not in quiz_data:
                raise ValueError("Missing 'questions' field in response")

            # Ensure each question has required fields
            for q in quiz_data["questions"]:
                if "question" not in q or "options" not in q or "correctAnswer" not in q:
                    raise ValueError("Question missing required fields")

                # Ensure options is a list of 4 items
                if not isinstance(q["options"], list) or len(q["options"]) != 4:
                    # Pad or trim options
                    options = q["options"] if isinstance(q["options"], list) else []
                    while len(options) < 4:
                        options.append("None of the above")
                    q["options"] = options[:4]

                # Ensure correctAnswer is valid index
                if not isinstance(q["correctAnswer"], int) or q["correctAnswer"] < 0 or q["correctAnswer"] >= 4:
                    q["correctAnswer"] = 0

            return {
                "title": quiz_data.get("title", "Generated Quiz"),
                "questions": quiz_data["questions"]
            }

        except Exception as e:
            logger.error(f"Error parsing quiz generation response: {e}")
            # Return fallback quiz
            return {
                "title": "Study Quiz",
                "questions": [
                    {
                        "question": "What is the main topic covered in the uploaded documents?",
                        "options": ["Topic A", "Topic B", "Topic C", "Topic D"],
                        "correctAnswer": 0,
                        "explanation": "Based on document analysis."
                    }
                ]
            }

    async def generate_explanation(
        self,
        question: str,
        correct_answer: str,
        context: str
    ) -> str:
        """
        Generate an explanation for why an answer is correct.
        """
        prompt = f"""Explain why the following answer is correct.

Question: {question}
Correct Answer: {correct_answer}
Context: {context}

Explanation:"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful tutor explaining quiz answers."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.5
        )

        return response.choices[0].message.content.strip()
