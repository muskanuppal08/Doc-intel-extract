"""Application settings and environment configuration."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Base Application
    PROJECT_NAME: str = "Document Processing & Question Extraction Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security & JWT
    SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-1234567890abcdef"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "pbnc_questions"
    POSTGRES_PORT: int = 5432
    USE_SQLITE: bool = False

    @computed_field
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.USE_SQLITE:
            base_dir = Path(__file__).resolve().parent.parent.parent
            return f"sqlite:///{base_dir}/app.db"
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis & Task Queue
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @computed_field
    def CELERY_BROKER_URL(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # File Storage
    STORAGE_BACKEND: str = "local"  # "local" or "s3"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    UPLOAD_DIR_NAME: str = "storage/uploads"
    CROPS_DIR_NAME: str = "storage/crops"
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    ]

    @computed_field
    def UPLOAD_DIR(self) -> Path:
        path = self.BASE_DIR / self.UPLOAD_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @computed_field
    def CROPS_DIR(self) -> Path:
        path = self.BASE_DIR / self.CROPS_DIR_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    # AI / Vision / OCR Engines
    OCR_ENGINE: str = "hybrid"  # "hybrid", "digital", "tesseract", "vision_ai", "mock"
    AI_PROVIDER: str = "mock"   # "mock", "gemini", "openai"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    TESSERACT_CMD: Optional[str] = None

    # Extraction Thresholds
    CONFIDENCE_THRESHOLD_REVIEW: float = 0.80  # Questions with score < 0.80 flagged for review
    CONFIDENCE_THRESHOLD_HIGH: float = 0.90


settings = Settings()
