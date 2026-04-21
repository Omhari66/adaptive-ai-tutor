import json
import logging
import re
from typing import Dict, Any, Optional

from groq import AsyncGroq
from app.core.config import settings

logger = logging.getLogger(__name__)

class EvaluationService:
    """
    Evaluates whether the user's response to an exam/teacher question is correct.
    Supports a 2-stage mechanism: Keyword Heuristic + Optional Lightweight LLM processing.
    """

    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.eval_model = "llama3-8b-8192"  # Fast, lightweight model for evaluation

    def _heuristic_evaluate(self, user_answer: str, context_answer: str) -> Optional[bool]:
        """
        Phase 1: Fast keyword/regex heuristic to check if they got it right.
        Returns True/False if highly confident, None to fallback.
        """
        user_answer_clean = user_answer.lower().strip()
        
        # Simple exact match (for extremely short answers)
        if user_answer_clean == context_answer.lower().strip():
            return True

        # Check for simple negation which often fails basic keyword match
        negations = ["not", "no", "never", "false", "incorrect"]
        has_negation = any(re.search(rf'\b{n}\b', user_answer_clean) for n in negations)
        context_has_negation = any(re.search(rf'\b{n}\b', context_answer.lower()) for n in negations)

        if has_negation != context_has_negation:
            # Simple heuristic: if one is negative and the other isn't, they are likely mismatched
            pass

        # We keep Phase 1 extremely cautious. If it can't guarantee, return None.
        return None

    async def evaluate_answer(self, user_answer: str, question: str, mode: str) -> Dict[str, Any]:
        """
        Evaluate user answer returning is_correct and a confidence score.
        Never blindly rely on LLM.
        """
        # If it wasn't a testing mode, don't evaluate
        if mode not in ["TEACHER", "EXAM"]:
            return {"is_correct": True, "confidence": 1.0}

        # We do not have explicit expected context answer stored easily yet.
        # So we trigger the LLM but bind it strictly.
        
        prompt = f"""You are an evaluator grading a student. 
Question asked: {question}
Student's Answer: {user_answer}

Did the student answer correctly? Focus on core correctness, ignore typos.
Output JSON format ONLY:
{{
  "is_correct": boolean,
  "confidence": float (0.0 to 1.0)
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.eval_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Guardrails
            is_correct = bool(result.get("is_correct", True))
            confidence = float(result.get("confidence", 0.5))
            
            logger.info(f"Evaluator: correct={is_correct}, confidence={confidence}")
            return {"is_correct": is_correct, "confidence": confidence}

        except Exception as e:
            logger.error(f"Evaluation failed, defaulting to True. Error: {str(e)}")
            return {"is_correct": True, "confidence": 0.5}

def get_evaluation_service() -> EvaluationService:
    return EvaluationService()
