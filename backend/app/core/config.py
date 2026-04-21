"""
Application configuration using pydantic-settings
Loads environment variables from .env file
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # --- Auth Configuration (ADD THESE) ---
    JWT_SECRET: str = Field(default="super-secret-key-12345", description="Secret key for JWT")
    JWT_EXPIRE_MINUTES: int = Field(default=10080, description="Token expiry in minutes (1 week)")

    # Groq Configuration
    GROQ_API_KEY: str = Field(default="", description="Groq API Key")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant", description="Groq model for generation")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", description="Local sentence-transformer embedding model")

    # Database Configuration
    DATABASE_URL: str = Field(default="postgresql://postgres:password@localhost:5432/rag_study_assistant")

    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Qdrant Vector Database
    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_API_KEY: Optional[str] = Field(default=None)
    QDRANT_COLLECTION_NAME: str = Field(default="study_documents")

    # File Storage
    UPLOAD_DIR: str = Field(default="./uploads")
    MAX_FILE_SIZE_MB: int = Field(default=50)

    # Server Configuration
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    DEBUG: bool = Field(default=True)

    # RAG Configuration
    VECTOR_SEARCH_TOP_K: int = Field(default=5)
    RERANK_TOP_K: int = Field(default=3)
    CHUNK_SIZE: int = Field(default=512)
    CHUNK_OVERLAP: int = Field(default=50)
    CONFIDENCE_THRESHOLD: float = Field(default=0.3)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # --- ADD THIS LINE ---
        extra = "ignore" 


# Ensure upload directory exists
settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)