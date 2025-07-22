"""
Container monitoring system for parallel Docker execution.
Provides real-time monitoring and health checks for running containers.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import time

from backend.common.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class ContainerMonitor:
    """Monitors Docker containers for parallel execution."""
    
    def __init__(self, redis_url: str = None):
        self.redis = get_redis_client(redis_url)
        self.monitoring = False
        self.check_interval = 5  # seconds
        
        # Key prefixes
        self.MONITOR_PREFIX = "monitor:container"
        self.HEALTH_PREFIX = "monitor:health"
        
    async def start_monitoring(self, job_id: str):
        """Start monitoring containers for a job."""
        self.monitoring = True
        await self._monitor_job_containers(job_id)
    
    async def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring = False
    
    async def _monitor_job_containers(self, job_id: str):
        """Monitor containers for a specific job."""
        while self.monitoring:
            try:
                await self._check_container_status(job_id)
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error monitoring containers for job {job_id}: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _check_container_status(self, job_id: str):
        """Check status of all containers for a job."""
        container_pattern = f"parallel:container:*"
        container_keys = self.redis.client.keys(container_pattern)
        
        for key in container_keys:
            container_data = self.redis.client.get(key)
            if not container_data:
                continue
                
            container_info = json.loads(container_data)
            if container_info.get("job_id") != job_id:
                continue
            
            # Update last check timestamp
            container_info["last_check"] = datetime.now(timezone.utc).isoformat()
            
            # Store container health info
            health_key = f"{self.HEALTH_PREFIX}:{job_id}:{container_info.get('container_id', 'unknown')}"
            health_data = {
                "container_id": container_info.get("container_id"),
                "job_id": job_id,
                "status": container_info.get("status", "unknown"),
                "last_check": container_info["last_check"],
                "use_case_id": container_info.get("use_case_id")
            }
            
            self.redis.client.setex(health_key, 3600, json.dumps(health_data))
            
            # Update container info
            self.redis.client.setex(key, 86400, json.dumps(container_info))
    
    def get_container_health(self, job_id: str) -> Dict[str, Any]:
        """Get health status of all containers for a job."""
        health_pattern = f"{self.HEALTH_PREFIX}:{job_id}:*"
        health_keys = self.redis.client.keys(health_pattern)
        
        health_status = {
            "total_containers": 0,
            "healthy_containers": 0,
            "unhealthy_containers": 0,
            "containers": []
        }
        
        for key in health_keys:
            health_data = self.redis.client.get(key)
            if health_data:
                health_info = json.loads(health_data)
                health_status["containers"].append(health_info)
                health_status["total_containers"] += 1
                
                # Simple health check based on last update
                last_check = datetime.fromisoformat(health_info.get("last_check", ""))
                if (datetime.now(timezone.utc) - last_check).seconds < 30:
                    health_status["healthy_containers"] += 1
                else:
                    health_status["unhealthy_containers"] += 1
        
        return health_status
    
    def get_progress_summary(self, job_id: str) -> Dict[str, Any]:
        """Get progress summary for parallel execution."""
        # Get queue status
        queue_key = f"parallel:queue:{job_id}"
        queue_length = self.redis.client.llen(queue_key)
        
        # Get container status
        container_pattern = f"parallel:container:*"
        container_keys = self.redis.client.keys(container_pattern)
        
        running = 0
        completed = 0
        failed = 0
        
        for key in container_keys:
            container_data = self.redis.client.get(key)
            if container_data:
                container_info = json.loads(container_data)
                if container_info.get("job_id") == job_id:
                    status = container_info.get("status", "unknown")
                    if status == "running":
                        running += 1
                    elif status == "completed":
                        completed += 1
                    elif status == "failed":
                        failed += 1
        
        return {
            "job_id": job_id,
            "queued_use_cases": queue_length,
            "running_containers": running,
            "completed_containers": completed,
            "failed_containers": failed,
            "estimated_remaining": queue_length + running,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_real_time_metrics(self, job_id: str) -> Dict[str, Any]:
        """Get real-time execution metrics."""
        metrics = self.get_progress_summary(job_id)
        
        # Add container health info
        health = self.get_container_health(job_id)
        metrics["container_health"] = health
        
        # Add performance metrics
        container_pattern = f"parallel:container:*"
        container_keys = self.redis.client.keys(container_pattern)
        
        total_runtime = 0
        completed_count = 0
        
        for key in container_keys:
            container_data = self.redis.client.get(key)
            if container_data:
                container_info = json.loads(container_data)
                if container_info.get("job_id") == job_id and container_info.get("completed_at"):
                    started = datetime.fromisoformat(container_info.get("started_at", ""))
                    completed = datetime.fromisoformat(container_info.get("completed_at"))
                    runtime = (completed - started).total_seconds()
                    total_runtime += runtime
                    completed_count += 1
        
        if completed_count > 0:
            metrics["avg_runtime_seconds"] = total_runtime / completed_count
        
        return metrics
    
    def get_container_logs(self, job_id: str, container_id: str) -> Optional[str]:
        """Get logs for a specific container."""
        log_key = f"parallel:log:{job_id}:{container_id}"
        return self.redis.client.get(log_key)
    
    def get_use_case_results(self, job_id: str, use_case_id: str) -> Optional[Dict[str, Any]]:
        """Get results for a specific use case."""
        result_key = f"parallel:result:{job_id}:{use_case_id}"
        result_data = self.redis.client.get(result_key)
        return json.loads(result_data) if result_data else None