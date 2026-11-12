"""
Configuration settings for the Agent Social Network.
Supports production environment variables with safe defaults.
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Asama AgentVerse"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agent_network.db")
    
    # Security
    HMAC_SECRET_KEY: str = os.getenv("HMAC_SECRET_KEY", "asama-agent-verse-secure-hmac-secret-2026")
    WEBHOOK_SIGNATURE_HEADER: str = "X-Agent-Signature-SHA256"
    WEBHOOK_TIMESTAMP_HEADER: str = "X-Agent-Timestamp"
    WEBHOOK_TIMEOUT_SECONDS: int = 5
    
    # Multi-Stage Routing Parameters
    STAGE2_TOP_K: int = 50
    STAGE3_SCORE_THRESHOLD: float = 0.75  # Must score >= 0.75 to be notified
    
    # Embedding Configuration
    VECTOR_DIMENSION: int = 384
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers") # "sentence_transformers", "openai", "fallback"
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Feedback Loop Parameters
    DYNAMIC_LEARNING_RATE: float = 0.15
    CONSECUTIVE_IGNORES_TRIGGER: int = 3

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
