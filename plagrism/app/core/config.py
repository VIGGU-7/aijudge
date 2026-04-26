from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Base Configuration
    PROJECT_NAME: str = "AI Judge - Plagiarism Detection"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "production"  # development, production, test
    
    # Server configuration (Cloud Run uses the PORT env var)
    PORT: int = int(os.getenv("PORT", 8080))
    HOST: str = "0.0.0.0"
    
    # GCP Project Configuration
    PROJECT_ID: str = "your-gcp-project-id"
    LOCATION: str = "us-central1"
    
    # Database Configuration (PostgreSQL + pgvector)
    DATABASE_URL: Optional[str] = None
    
    # Storage Configuration (GCS)
    STORAGE_BUCKET: str = "ai-judge-submissions"
    RAW_PREFIX: str = "raw"
    PROCESSED_PREFIX: str = "processed"
    
    # Pub/Sub Configuration
    SUBMISSION_TOPIC: str = "submission-created"
    
    # Security: CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
