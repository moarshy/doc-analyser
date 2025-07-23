import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import logging
from celery.result import AsyncResult

from backend.worker.celery_app import celery_app
from backend.models.analysis import AnalysisJob, AnalysisStatus
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
        user_id: str,
        project_id: Optional[str] = None,
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
        
        # Store job in Redis using simplified structure
        job_data = {
            "status": "pending",
            "total_use_cases": 0,
            "completed": 0,
            "failed": 0,
            "pending": 0,
            "job_params": {
                "repository_url": url,
                "branch": branch,
                "include_folders": include_folders,
                "job_id": str(job_id),
                "user_id": user_id,
                "project_id": project_id,
            },
            "use_cases": {},
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        }
        
        if not self.redis.store_job(job_id, job_data):
            logger.error(f"Failed to store job {job_id} in Redis")
            raise RuntimeError("Failed to store job")
        else:
            logger.info(f"Successfully stored job {job_id} in Redis")

        # Link job to user and project
        from backend.backend.services.auth_service import auth_service
        auth_service.link_job_to_user(user_id, str(job_id))
        
        if project_id:
            from backend.services.project_service import project_service
            project_service.link_job_to_project(project_id, str(job_id))

        # Queue the orchestrated analysis task
        task = celery_app.send_task(
            "orchestrate_analysis",
            args=[
                str(job_id),
                url,
                branch,
                include_folders,
            ],
            task_id=str(job_id)  # Use job_id as task_id for consistency
        )
        logger.info(f"Analysis task queued: {task.id}")
        return job_id

    async def get_job_status(self, job_id: UUID) -> AnalysisJob:
        """Get the current status of an analysis job."""
        # Get job data from Redis
        job_data = self.redis.get_job(job_id)
        if not job_data:
            raise ValueError(f"Job {job_id} not found")

        # Create AnalysisJob from Redis data using simplified structure
        job_params = job_data.get("job_params", {})
        job = AnalysisJob(
            id=job_id,
            repository_url=job_params.get("repository_url", ""),
            branch=job_params.get("branch", "main"),
            include_folders=job_params.get("include_folders", ["docs"]),
            status=AnalysisStatus(job_data.get("status", "pending")),
            created_at=datetime.fromisoformat(job_data.get("created_at", datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(job_data.get("updated_at", datetime.utcnow().isoformat())),
            results=job_data.get("results"),
            error=job_data.get("error"),
            use_cases=list(job_data.get("use_cases", {}).values())
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
                        "status": "completed",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })
                    self.redis.store_job(job_id, job_data)
                else:
                    error = str(task.result)
                    job.error = error
                    job.status = AnalysisStatus.FAILED
                    
                    # Update Redis with failed status
                    job_data.update({
                        "status": "failed",
                        "error": error,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    })
                    self.redis.store_job(job_id, job_data)
                
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

    async def list_user_jobs(self, user_id: str, skip: int = 0, limit: int = 100) -> List[AnalysisJob]:
        """List analysis jobs for a specific user."""
        from backend.backend.services.auth_service import auth_service
        
        # Get user's job IDs
        job_ids = auth_service.get_user_jobs(user_id)
        
        jobs = []
        for job_id_str in job_ids[skip : skip + limit]:
            try:
                job_id = UUID(job_id_str)
                job = await self.get_job_status(job_id)
                jobs.append(job)
            except ValueError:
                logger.warning(f"Invalid job ID for user {user_id}: {job_id_str}")
                continue
        
        return jobs

