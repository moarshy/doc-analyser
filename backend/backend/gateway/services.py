import asyncio
import json
from datetime import datetime
from typing import Dict, List
from uuid import UUID, uuid4

from celery.result import AsyncResult

from backend.worker.celery_app import celery_app
from .models import AnalysisJob, AnalysisStatus


class AnalysisService:
    def __init__(self):
        self._jobs: Dict[UUID, AnalysisJob] = {}

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
        self._jobs[job_id] = job

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

        return job_id

    async def get_job_status(self, job_id: UUID) -> AnalysisJob:
        """Get the current status of an analysis job."""
        if job_id not in self._jobs:
            raise ValueError(f"Job {job_id} not found")

        job = self._jobs[job_id]
        
        # Check Celery task status
        if job.status in [AnalysisStatus.PENDING, AnalysisStatus.PROCESSING]:
            task_id = str(job_id)
            task = AsyncResult(task_id, app=celery_app)
            
            if task.ready():
                if task.successful():
                    result = task.result
                    job.results = result
                    job.status = AnalysisStatus.COMPLETED
                    job.use_cases = result.get("use_cases", [])
                else:
                    job.error = str(task.result)
                    job.status = AnalysisStatus.FAILED
                
                job.updated_at = datetime.utcnow()

        return job

    async def list_jobs(self, skip: int = 0, limit: int = 100) -> List[AnalysisJob]:
        """List all analysis jobs."""
        jobs = list(self._jobs.values())
        return jobs[skip : skip + limit]

    def update_job(self, job_id: UUID, **kwargs):
        """Update a job's status and results."""
        if job_id in self._jobs:
            job = self._jobs[job_id]
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            job.updated_at = datetime.utcnow()