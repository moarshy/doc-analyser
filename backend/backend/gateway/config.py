from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server settings
    APP_HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Analysis settings
    MAX_CONCURRENT_JOBS: int = 3
    ANALYSIS_TIMEOUT: int = 3600*2  # 2 hours

    class Config:
        env_file = ".env"


settings = Settings()