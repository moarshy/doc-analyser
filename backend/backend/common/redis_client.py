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
    """Unified Redis client for all application data storage."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize Redis client.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.client = redis.from_url(redis_url, decode_responses=True)
        
        # Unified key patterns for all data types
        self.JOB_KEY = "job:{job_id}"
        self.USER_KEY = "user:{user_id}"
        self.PROJECT_KEY = "project:{project_id}"
        self.USER_JOBS_KEY = "user_jobs:{user_id}"
        self.USER_PROJECTS_KEY = "user_projects:{user_id}"
        self.PROJECT_JOBS_KEY = "project_jobs:{project_id}"
        
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
            self.client.set(
                key,
                json.dumps(job_data, default=str)
            )
            logger.info(f"Stored job {job_id} in Redis with key {key}")
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
            if data:
                logger.debug(f"Found job {job_id} in Redis")
                return json.loads(data)
            else:
                logger.warning(f"Job {job_id} not found in Redis (key: {key})")
                return None
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
            job_data = self.get_job(job_id)
            
            if job_data is None:
                logger.warning(f"Job {job_id} not found in Redis when trying to update field {field}, creating new job data")
                job_data = {
                    "status": "pending",
                    "total_use_cases": 0,
                    "completed": 0,
                    "failed": 0,
                    "pending": 0,
                    "use_cases": {},
                    "created_at": str(datetime.now(timezone.utc))
                }
            
            job_data[field] = value
            job_data["updated_at"] = str(datetime.now(timezone.utc))
            
            self.client.set(
                key,
                json.dumps(job_data, default=str)
            )
            logger.debug(f"Updated job {job_id} field {field}")
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
            
            self.client.set(
                key,
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

    def cleanup_old_jobs(self, older_than_days: int = 30) -> int:
        """Clean up old job data manually.
        
        Args:
            older_than_days: Delete jobs older than this many days
            
        Returns:
            Number of keys cleaned up
        """
        try:
            from datetime import timedelta
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            job_ids = self.list_jobs()
            deleted_count = 0
            
            for job_id in job_ids:
                job_data = self.get_job(UUID(job_id))
                if job_data and job_data.get('created_at'):
                    created_at = datetime.fromisoformat(job_data['created_at'])
                    if created_at < cutoff_time:
                        self.delete_job_data(UUID(job_id))
                        deleted_count += 1
            
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to cleanup old jobs: {e}")
            return 0

    # User management methods
    def store_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Store user data using JSON format for consistency."""
        try:
            key = self.USER_KEY.format(user_id=user_id)
            self.client.set(key, json.dumps(user_data, default=str))
            logger.info(f"Stored user {user_id} in Redis")
            return True
        except RedisError as e:
            logger.error(f"Failed to store user {user_id}: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user data from Redis."""
        try:
            key = self.USER_KEY.format(user_id=user_id)
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None

    def update_user_field(self, user_id: str, field: str, value: Any) -> bool:
        """Update a specific field in user data."""
        try:
            user_data = self.get_user(user_id)
            if user_data is None:
                return False
            
            user_data[field] = value
            user_data["updated_at"] = str(datetime.now(timezone.utc))
            return self.store_user(user_id, user_data)
        except Exception as e:
            logger.error(f"Failed to update user field {user_id}.{field}: {e}")
            return False

    # Project management methods
    def store_project(self, project_id: str, project_data: Dict[str, Any]) -> bool:
        """Store project data using JSON format for consistency."""
        try:
            key = self.PROJECT_KEY.format(project_id=project_id)
            self.client.set(key, json.dumps(project_data, default=str))
            logger.info(f"Stored project {project_id} in Redis")
            return True
        except RedisError as e:
            logger.error(f"Failed to store project {project_id}: {e}")
            return False

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve project data from Redis."""
        try:
            key = self.PROJECT_KEY.format(project_id=project_id)
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    def update_project_field(self, project_id: str, field: str, value: Any) -> bool:
        """Update a specific field in project data."""
        try:
            project_data = self.get_project(project_id)
            if project_data is None:
                return False
            
            project_data[field] = value
            project_data["updated_at"] = str(datetime.now(timezone.utc))
            return self.store_project(project_id, project_data)
        except Exception as e:
            logger.error(f"Failed to update project field {project_id}.{field}: {e}")
            return False

    # Relationship management methods
    def add_user_job(self, user_id: str, job_id: str) -> bool:
        """Add job to user's job list."""
        try:
            key = self.USER_JOBS_KEY.format(user_id=user_id)
            timestamp = datetime.now(timezone.utc).timestamp()
            self.client.zadd(key, {job_id: timestamp})
            return True
        except RedisError as e:
            logger.error(f"Failed to add job {job_id} to user {user_id}: {e}")
            return False

    def get_user_jobs_list(self, user_id: str) -> List[str]:
        """Get all job IDs for a user."""
        try:
            key = self.USER_JOBS_KEY.format(user_id=user_id)
            return self.client.zrevrange(key, 0, -1)  # Newest first
        except RedisError as e:
            logger.error(f"Failed to get jobs for user {user_id}: {e}")
            return []

    def add_user_project(self, user_id: str, project_id: str) -> bool:
        """Add project to user's project list."""
        try:
            key = self.USER_PROJECTS_KEY.format(user_id=user_id)
            timestamp = datetime.now(timezone.utc).timestamp()
            self.client.zadd(key, {project_id: timestamp})
            return True
        except RedisError as e:
            logger.error(f"Failed to add project {project_id} to user {user_id}: {e}")
            return False

    def get_user_projects_list(self, user_id: str) -> List[str]:
        """Get all project IDs for a user."""
        try:
            key = self.USER_PROJECTS_KEY.format(user_id=user_id)
            return self.client.zrevrange(key, 0, -1)  # Newest first
        except RedisError as e:
            logger.error(f"Failed to get projects for user {user_id}: {e}")
            return []

    def add_project_job(self, project_id: str, job_id: str) -> bool:
        """Add job to project's job list."""
        try:
            key = self.PROJECT_JOBS_KEY.format(project_id=project_id)
            timestamp = datetime.now(timezone.utc).timestamp()
            self.client.zadd(key, {job_id: timestamp})
            return True
        except RedisError as e:
            logger.error(f"Failed to add job {job_id} to project {project_id}: {e}")
            return False

    def get_project_jobs_list(self, project_id: str) -> List[str]:
        """Get all job IDs for a project."""
        try:
            key = self.PROJECT_JOBS_KEY.format(project_id=project_id)
            return self.client.zrevrange(key, 0, -1)  # Newest first
        except RedisError as e:
            logger.error(f"Failed to get jobs for project {project_id}: {e}")
            return []


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
                from backend.common.config import config
                redis_url = config.REDIS_URL
            except ImportError:
                # Fallback for testing
                redis_url = "redis://localhost:6379/0"
        redis_client = RedisClient(redis_url)
    return redis_client