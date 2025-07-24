import os
from typing import List
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    # Server settings
    APP_HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Analysis settings
    MAX_CONCURRENT_JOBS: int = 3
    ANALYSIS_TIMEOUT: int = 7200  # 2 hours

    # Auth0 settings
    AUTH0_DOMAIN: str = ""
    AUTH0_AUDIENCE: str = ""

    # Data directory
    DATA_DIR: str = os.getenv("DATA_DIR", "/Users/arshath/play/naptha/doc-analyser/data")

    # Docker sandboxsettings
    DOCKER_IMAGE: str = "python:3.11-slim"
    DOCKER_SANDBOX_IMAGE: str = "doc-analyser-sandbox:latest"
    DOCKER_NETWORK: str = "doc-analyser"

    # Claude Code settings
    CLAUDE_CODE_TIMEOUT: int = 3600 * 3 # 3 hours
    ANTHROPIC_AUTH_TOKEN: str = ""
    ANTHROPIC_BASE_URL: str = ""

    # Git settings
    GIT_CLONE_TIMEOUT: int = 300  # 5 minutes

    # Logging
    LOG_LEVEL: str = "INFO"

    # Pool settings
    MAX_WORKER_POOL_SIZE: int = 5
    WORKER_MEMORY_LIMIT: str = "1g"
    WORKER_CPU_LIMIT: str = "0.2"

    @property
    def VOLUME_PATH(self) -> str:
        """Path to the volume directory for Docker containers."""
        return os.path.join(self.DATA_DIR, "volumes")

    def setup_directories(self):
        """Ensure all required directories exist."""
        os.makedirs(self.VOLUME_PATH, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)

    class Config:
        env_file = [
            ".env",
            "backend/.env",
            os.path.join(os.path.dirname(__file__), ".env"),
            os.path.join(os.path.dirname(__file__), "..", ".env"),
        ]
        extra = "ignore"

# Create singleton instance
config = Config()

# Backward compatibility
settings = config