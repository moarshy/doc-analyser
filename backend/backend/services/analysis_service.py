import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import logging

from backend.models.analysis import AnalysisJob, AnalysisStatus
from backend.common.redis_client import get_redis_client

# Import celery components only when needed to avoid import errors
try:
    from celery.result import AsyncResult
    from backend.worker.celery_app import celery_app
    from backend.worker.logger import tasks_logger
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None
    tasks_logger = None

logger = logging.getLogger("backend.gateway.services")

class AnalysisService:
    def __init__(self):
        self.redis = get_redis_client()
    
    def _extract_use_cases(self, use_cases_data):
        """
        Extract use cases from Redis data structure correctly.
        Redis stores: {"0": {"name": "...", "data": {...}, "status": "..."}, "1": {...}}
        We need: [{"name": "...", "description": "...", ...}, ...]
        """
        if not use_cases_data:
            return []
        
        
        if isinstance(use_cases_data, dict):
            extracted_use_cases = []
            for key, value in use_cases_data.items():
                if isinstance(value, dict):
                    # Check if this has the expected structure with 'data' field
                    if "data" in value:
                # Merge the top-level metadata with the data
                        use_case = {
                            **value["data"],  # Use case data (name, description, etc.)
                            "status": value.get("status"),  # Status from top level
                            "execution_time_seconds": value.get("execution_time_seconds"),
                            "container_logs": value.get("container_logs"),
                            "start_time": value.get("start_time"),
                            "end_time": value.get("end_time"),
                        }
                        
                        extracted_use_cases.append(use_case)
                    elif "name" in value:
                        # Direct use case data
                        extracted_use_cases.append(value)
                    else:
                        # Unknown structure, add as-is
                        extracted_use_cases.append(value)
                else:
                    # Non-dict value, add as-is
                    extracted_use_cases.append(value)

            return extracted_use_cases
        
        elif isinstance(use_cases_data, list):
            # Already a list
            return use_cases_data
        
        else:
            # Unexpected type, convert to list
            return [use_cases_data]

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
        from backend.services.auth_service import auth_service
        auth_service.link_job_to_user(user_id, str(job_id))
        
        if project_id:
            from backend.services.project_service import project_service
            project_service.link_job_to_project(project_id, str(job_id))

        # Queue the orchestrated analysis task (if celery is available)
        if CELERY_AVAILABLE and celery_app:
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
        else:
            logger.warning("Celery not available - analysis task not queued")
        
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
            use_cases=self._extract_use_cases(job_data.get("use_cases", {}))
        )
        
        # Check Celery task status for updates (if celery is available)
        if CELERY_AVAILABLE and celery_app and job.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
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

    async def list_user_jobs(self, user_id: str) -> List[AnalysisJob]:
        """List analysis jobs for a specific user."""
        from backend.services.auth_service import auth_service
        
        # Get user's job IDs
        job_ids = auth_service.get_user_jobs(user_id)
        
        jobs = []
        for job_id_str in job_ids:
            try:
                job_id = UUID(job_id_str)
                job = await self.get_job_status(job_id)
                jobs.append(job)
            except ValueError:
                logger.warning(f"Invalid job ID for user {user_id}: {job_id_str}")
                continue
        
        return jobs

