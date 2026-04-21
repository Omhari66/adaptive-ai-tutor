"""
Shared embedding service using singleton pattern
Prevents redundant model loading across services
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer, CrossEncoder
from app.core.config import settings


class EmbeddingService:
    """
    Singleton embedding service for generating vector embeddings.
    Loads the model once and reuses it across all requests.
    """

    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    _reranker: Optional[CrossEncoder] = None

    def __new__(cls) -> 'EmbeddingService':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self._model is None:
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._model

    def _get_reranker(self) -> CrossEncoder:
        """Lazy load the reranker model"""
        if self._reranker is None:
            # Using same model referenced in rag_service
            self._reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        return self._reranker

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        Returns list of floats compatible with Qdrant.
        """
        model = self._get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        """
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32)
        return embeddings.tolist()

    def rerank_pairs(self, pairs: List[List[str]]) -> List[float]:
        """
        Rerank query-document pairs using the cross encoder model.
        """
        model = self._get_reranker()
        scores = model.predict(pairs)
        return [float(score) for score in scores]


# Global singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
