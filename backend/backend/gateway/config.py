import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server settings
    APP_HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Analysis settings
    MAX_CONCURRENT_JOBS: int = 3
    ANALYSIS_TIMEOUT: int = 3600*2  # 2 hours

    # Auth0 settings
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""

    class Config:
        # Try multiple possible .env file locations
        env_file = [
            ".env",  # Current directory
            "backend/.env",  # If running from parent
            os.path.join(os.path.dirname(__file__), ".env"),  # Same dir as config.py
            os.path.join(os.path.dirname(__file__), "..", ".env"),  # Parent of gateway dir
        ]
        extra = "ignore"  # Ignore extra fields from env file


settings = Settings()