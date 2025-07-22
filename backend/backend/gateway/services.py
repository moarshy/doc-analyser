import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import logging
from celery.result import AsyncResult

from backend.worker.celery_app import celery_app
from backend.gateway.models import AnalysisJob, AnalysisStatus
from backend.common.redis_client import get_redis_client
from backend.worker.logger import tasks_logger

logger = logging.getLogger("backend.gateway.services")

class AnalysisService:
    def __init__(self):
        self.redis = get_redis_client()

    async def submit_analysis(
        self,
        url: str,
        branch: str,
        include_folders: List[str],
    ) -> UUID:
        """Submit a repository for analysis."""
        job_id = uuid4()
        
        # Create job record
        job = AnalysisJob(
            id=job_id,
            repository_url=url,
            branch=branch,
            include_folders=include_folders,
            status=AnalysisStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Store job in Redis
        job_data = {
            "id": str(job_id),
            "repository_url": url,
            "branch": branch,
            "include_folders": include_folders,
            "status": AnalysisStatus.PENDING.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }
        
        if not self.redis.store_job(job_id, job_data):
            logger.error(f"Failed to store job {job_id} in Redis")
            raise RuntimeError("Failed to store job")

        # Store initial status
        self.redis.store_job_status(job_id, AnalysisStatus.PENDING.value, {
            "message": "Job submitted",
            "task_id": str(job_id)
        })

        # Queue the analysis task
        task = celery_app.send_task(
            "analyze_repository",
            args=[
                str(job_id),
                url,
                branch,
                include_folders,
            ],
        )
        logger.info(f"Analysis task queued: {task.id}")
        return job_id

    async def get_job_status(self, job_id: UUID) -> AnalysisJob:
        """Get the current status of an analysis job."""
        # Get job data from Redis
        job_data = self.redis.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")

        # Create AnalysisJob from Redis data
        job = AnalysisJob(
            id=UUID(job_data["id"]),
            repository_url=job_data["repository_url"],
            branch=job_data["branch"],
            include_folders=job_data["include_folders"],
            status=AnalysisStatus(job_data["status"]),
            created_at=datetime.fromisoformat(job_data["created_at"]),
            updated_at=datetime.fromisoformat(job_data["updated_at"]),
            results=job_data.get("results"),
            error=job_data.get("error"),
            use_cases=job_data.get("use_cases", [])
        )
        
        # Check Celery task status for updates
        if job.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
            task_id = str(job_id)
            task = AsyncResult(task_id, app=celery_app)
            
            if task.ready():
                if task.successful():
                    result = task.result
                    job.results = result
                    job.status = AnalysisStatus.COMPLETED
                    job.use_cases = result.get("use_cases", [])
                    
                    # Update Redis with completed status
                    job_data.update({
                        "status": AnalysisStatus.COMPLETED.value,
                        "results": result,
                        "use_cases": result.get("use_cases", []),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })
                    self.redis.store_job(job_id, job_data)
                    self.redis.store_job_status(job_id, AnalysisStatus.COMPLETED.value, {
                        "message": "Analysis completed",
                        "result": result
                    })
                else:
                    error = str(task.result)
                    job.error = error
                    job.status = AnalysisStatus.FAILED
                    
                    # Update Redis with failed status
                    job_data.update({
                        "status": AnalysisStatus.FAILED.value,
                        "error": error,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })
                    self.redis.store_job(job_id, job_data)
                    self.redis.store_job_status(job_id, AnalysisStatus.FAILED.value, {
                        "message": "Analysis failed",
                        "error": error
                    })
                
                job.updated_at = datetime.utcnow()

        return job

    async def list_jobs(self, skip: int = 0, limit: int = 100) -> List[AnalysisJob]:
        """List all analysis jobs."""
        # Get job IDs from Redis
        job_ids = self.redis.list_jobs()
        
        jobs = []
        for job_id_str in job_ids[skip : skip + limit]:
            try:
                job_id = UUID(job_id_str)
                job = await self.get_job_status(job_id)
                jobs.append(job)
            except ValueError:
                logger.warning(f"Invalid job ID in Redis: {job_id_str}")
                continue
        
        return jobs

    async def update_job_status(self, job_id: UUID, status: str, **kwargs):
        """Update job status in Redis."""
        job_data = self.redis.get_job(job_id)
        if job_data:
            job_data.update({
                "status": status,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                **kwargs
            })
            self.redis.store_job(job_id, job_data)
            self.redis.store_job_status(job_id, status, kwargs)

    def update_job(self, job_id: UUID, **kwargs):
        """Update a job's status and results."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.utcnow()