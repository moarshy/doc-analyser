"""
Redis cleanup utilities for the doc analyser system.
"""
import logging
from backend.common.redis_client import get_redis_client

logger = logging.getLogger(__name__)

def cleanup_all_jobs():
    """Clean up all job data from Redis."""
    redis = get_redis_client()
    try:
        # Get all job keys
        job_keys = redis.list_jobs()
        
        # Delete all job data
        for job_id in job_keys:
            redis.delete_job_data(job_id)
            
        logger.info(f"Cleaned up {len(job_keys)} jobs from Redis")
        return len(job_keys)
    except Exception as e:
        logger.error(f"Failed to cleanup jobs: {e}")
        return 0

def cleanup_expired_jobs():
    """Clean up expired job data from Redis."""
    redis = get_redis_client()
    return redis.cleanup_expired_jobs()

if __name__ == "__main__":
    # Run cleanup when executed directly
    count = cleanup_all_jobs()
    print(f"Cleaned up {count} jobs from Redis")