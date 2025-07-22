import logging
import os
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Set up a logger with consistent formatting."""
    
    logger = logging.getLogger(name)
    
    if logger.hasHandlers():
        return logger
    
    # Set log level from environment or config
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level))
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Create module-level loggers
analysis_logger = setup_logger("worker.analysis")
tasks_logger = setup_logger("worker.tasks")
docker_logger = setup_logger("worker.docker")
use_case_logger = setup_logger("worker.use_case")