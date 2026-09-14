"""
Application configuration.

All configuration is loaded from environment variables (via a .env file in
development). Nothing here is hardcoded - see .env.example for the full list
of variables this application expects.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "AI Placement Management System API"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # Example: mysql+pymysql://user:password@localhost:3306/placement_db
    DATABASE_URL: str

    # --- Security / JWT ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # --- CORS ---
    # Comma-separated list of allowed origins, e.g.
    # "http://localhost:3000,http://127.0.0.1:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- AI / LLM ---
    AI_API_KEY: str = ""
    AI_MODEL_NAME: str = "claude-sonnet-4-6"

    # --- File uploads ---
    RESUME_UPLOAD_DIR: str = "uploads/resumes"
    MAX_RESUME_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. Import this instead of instantiating Settings()
    directly so the environment is only parsed once per process.
    """
    return Settings()
