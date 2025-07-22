"""
Redis client configuration and utilities for the doc analyser system.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from uuid import UUID
from pathlib import Path
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for storing analysis job data and status."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)
        
        # Simplified single key per job
        self.JOB_KEY = "job:{job_id}"
        
        # Set default TTL for job data (5 days)
        self.DEFAULT_TTL = 86400 * 5
        
    def ping(self) -> bool:
        """Check if Redis is available."""
        try:
            return self.client.ping()
        except RedisError as e:
            logger.error(f"Redis ping failed: {e}")
            return False
    
    def store_job(self, job_id: UUID, job_data: Dict[str, Any]) -> bool:
        """Store job data in Redis using simplified single key structure.
        
        Args:
            job_id: Unique job identifier
            job_data: Job data to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self.JOB_KEY.format(job_id=job_id)
            self.client.setex(
                key,
                self.DEFAULT_TTL,
                json.dumps(job_data, default=str)
            )
            return True
        except RedisError as e:
            logger.error(f"Failed to store job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve job data from Redis using simplified key.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job data if found, None otherwise
        """
        try:
            key = self.JOB_KEY.format(job_id=job_id)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except RedisError as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode job data for {job_id}: {e}")
            return None
    
    def update_job_field(self, job_id: UUID, field: str, value: Any) -> bool:
        """Update a specific field in job data.
        
        Args:
            job_id: Unique job identifier
            field: Field name to update
            value: Field value
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self.JOB_KEY.format(job_id=job_id)
            job_data = self.get_job(job_id) or {}
            job_data[field] = value
            job_data["updated_at"] = str(datetime.now(timezone.utc))
            
            self.client.setex(
                key,
                self.DEFAULT_TTL,
                json.dumps(job_data, default=str)
            )
            return True
        except RedisError as e:
            logger.error(f"Failed to update job field {job_id}.{field}: {e}")
            return False

    def initialize_job(self, job_id: UUID, repository_url: str, branch: str, 
                      include_folders: List[str], repo_path: str, data_path: str) -> bool:
        """Initialize job with all parameters.
        
        Args:
            job_id: Unique job identifier
            repository_url: Repository URL
            branch: Git branch
            include_folders: Folders to include
            repo_path: Local repository path
            data_path: Local data output path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self.JOB_KEY.format(job_id=job_id)
            job_data = {
                "status": "pending",
                "total_use_cases": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
                "job_params": {
                    "repository_url": repository_url,
                    "branch": branch,
                    "include_folders": include_folders,
                    "job_id": str(job_id),
                    "repo_path": repo_path,
                    "data_path": data_path,
                    "job_id_path": str(Path(data_path).parent)
                },
                "use_cases": {},
                "containers": {},
                "created_at": str(datetime.now(timezone.utc)),
                "updated_at": str(datetime.now(timezone.utc))
            }
            
            self.client.setex(
                key,
                self.DEFAULT_TTL,
                json.dumps(job_data, default=str)
            )
            return True
        except RedisError as e:
            logger.error(f"Failed to initialize job {job_id}: {e}")
            return False

    def delete_job_data(self, job_id: UUID) -> bool:
        """Delete job data from Redis.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            key = self.JOB_KEY.format(job_id=job_id)
            self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Failed to delete data for job {job_id}: {e}")
            return False

    def list_jobs(self, pattern: str = "*") -> List[str]:
        """List all job IDs in Redis.
        
        Args:
            pattern: Pattern to match job IDs
            
        Returns:
            List of job IDs
        """
        try:
            keys = self.client.keys("job:{}".format(pattern))
            return [key.replace("job:", "") for key in keys]
        except RedisError as e:
            logger.error(f"Failed to list jobs: {e}")
            return []

    def cleanup_expired_jobs(self) -> int:
        """Clean up expired job data.
        
        Returns:
            Number of keys cleaned up (Redis handles automatically)
        """
        # Redis handles expiration automatically with TTL
        return 0


# Global Redis client instance
redis_client = None


def get_redis_client(redis_url: str = None) -> RedisClient:
    """Get the global Redis client instance.
    
    Args:
        redis_url: Optional Redis URL, defaults to config.REDIS_URL
        
    Returns:
        RedisClient instance
    """
    global redis_client
    if redis_client is None:
        if redis_url is None:
            try:
                from backend.worker.config import config
                redis_url = config.REDIS_URL
            except ImportError:
                # Fallback for testing
                redis_url = "redis://localhost:6379/0"
        redis_client = RedisClient(redis_url)
    return redis_client