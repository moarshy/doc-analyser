import os
from typing import List


class WorkerConfig:
    # Redis settings
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Docker settings
    DOCKER_IMAGE = os.getenv("DOCKER_IMAGE", "python:3.11-slim")
    DOCKER_SANDBOX_IMAGE = os.getenv("DOCKER_SANDBOX_IMAGE", "doc-analyser-sandbox:latest")
    DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "doc-analyser")
    
    # Analysis settings
    MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "3"))
    ANALYSIS_TIMEOUT = int(os.getenv("ANALYSIS_TIMEOUT", "7200"))  # 2 hours
    
    # Data directory settings
    DATA_DIR = os.getenv("DATA_DIR", "/Users/arshath/play/naptha/doc-analyser/data")  # Base data directory
    
    # Claude Code settings
    CLAUDE_CODE_TIMEOUT = int(os.getenv("CLAUDE_CODE_TIMEOUT", "3600"))  # 1 hour
    
    # Git settings
    GIT_CLONE_TIMEOUT = int(os.getenv("GIT_CLONE_TIMEOUT", "300"))  # 5 minutes
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def setup(cls):
        """Ensure required directories exist."""
        os.makedirs(cls.VOLUME_PATH, exist_ok=True)


# Create singleton instance
config = WorkerConfig()