import os
from pathlib import Path
from typing import List, Dict, Any
import json
from datetime import datetime, timezone
from uuid import UUID
from celery import Task
from git import Repo

from backend.worker.celery_app import celery_app
from backend.worker.config import WorkerConfig, config
from backend.worker.docker_runner import DockerRunner
from backend.worker.logger import tasks_logger
from backend.common.redis_client import get_redis_client


tasks_logger.info(f"Worker config: {config.__dict__}")

class AnalysisTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        tasks_logger.error(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        tasks_logger.info(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)




@celery_app.task(base=AnalysisTask, bind=True, name="extract_use_cases")
def extract_use_cases(
    self,
    job_id: str,
    repo_path: str,
    include_folders: List[str],
    output_dir: str,
) -> List[Dict[str, Any]]:
    """Extract use cases from repository documentation."""
    
    redis_client = get_redis_client()
    
    try:
        redis_client.update_job_field(UUID(job_id), "status", "extracting_use_cases")
        self.update_state(state="PROCESSING", meta={"status": "Running extraction in Docker"})
        
        # Run extraction in Docker
        docker_runner = DockerRunner()
        extraction_result = docker_runner.extract_use_cases(
            job_id=job_id,
            repo_path=repo_path,
            include_folders=include_folders,
            output_dir=output_dir
        )
        
        # Read extracted use cases
        use_cases_path = os.path.join(output_dir, "use_cases.json")
        use_cases = []
        if os.path.exists(use_cases_path):
            with open(use_cases_path) as f:
                data = json.load(f)
                use_cases = data.get("use_cases", [])
        
        return use_cases
        
    except Exception as e:
        redis_client.update_job_field(UUID(job_id), "status", "extraction_failed")
        redis_client.update_job_field(UUID(job_id), "error", str(e))
        raise RuntimeError(str(e))


@celery_app.task(base=AnalysisTask, bind=True, name="orchestrate_analysis")
def orchestrate_analysis(
    self,
    job_id: str,
    repository_url: str,
    branch: str = "main",
    include_folders: List[str] = None,
) -> Dict[str, Any]:
    """Single task that orchestrates the entire analysis workflow with Docker pool."""
    if include_folders is None:
        include_folders = ["docs"]
    
    redis_client = get_redis_client()
    
    try:
        # Initialize job directories
        data_dir = os.path.join(WorkerConfig.DATA_DIR, job_id)
        repo_dir = os.path.join(data_dir, "repo")
        output_dir = os.path.join(data_dir, "data")
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(repo_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Update job with paths and status
        redis_client.update_job_field(UUID(job_id), "repo_path", repo_dir)
        redis_client.update_job_field(UUID(job_id), "data_path", output_dir)
        redis_client.update_job_field(UUID(job_id), "status", "cloning")
        self.update_state(state="PROCESSING", meta={"status": "Cloning repository"})
        
        # Clone repository
        repo = Repo.clone_from(repository_url, repo_dir, branch=branch)
        
        # Update status to extracting
        redis_client.update_job_field(UUID(job_id), "status", "extracting")
        self.update_state(state="PROCESSING", meta={"status": "Extracting use cases"})
        
        # Run extraction
        docker_runner = DockerRunner()
        extraction_result = docker_runner.extract_use_cases(
            job_id=job_id,
            repo_path=repo_dir,
            include_folders=include_folders,
            output_dir=output_dir
        )
        
        # Read extracted use cases
        use_cases_path = os.path.join(output_dir, "use_cases.json")
        use_cases = []
        if os.path.exists(use_cases_path):
            with open(use_cases_path) as f:
                data = json.load(f)
                use_cases = data.get("use_cases", [])
        
        if not use_cases:
            redis_client.update_job_field(UUID(job_id), "status", "completed")
            return {
                "job_id": job_id,
                "repository": repository_url,
                "branch": branch,
                "use_cases": [],
                "status": "completed",
                "message": "No use cases found in repository"
            }
        
        # Update Redis with extracted use cases
        job_data = redis_client.get_job(UUID(job_id))
        if job_data:
            job_data["use_cases"] = {str(i): {
                "name": uc.get("name", f"Use Case {i}"),
                "status": "pending",
                "data": uc
            } for i, uc in enumerate(use_cases)}
            job_data["total_use_cases"] = len(use_cases)
            job_data["pending"] = len(use_cases)
            job_data["completed"] = 0
            job_data["failed"] = 0
            job_data["status"] = "executing"
            redis_client.store_job(UUID(job_id), job_data)
        
        # Execute use cases with Docker pool
        redis_client.update_job_field(UUID(job_id), "status", "executing")
        self.update_state(state="PROCESSING", meta={"status": "Executing use cases with Docker pool"})
        
        results = docker_runner.execute_use_cases_with_pool(
            job_id=job_id,
            use_cases=use_cases,
            repo_path=repo_dir,
            output_dir=output_dir,
            include_folders=include_folders,
            pool_size=5,
            redis_client=redis_client,
            task_context=self  # Pass task context for status updates
        )
        
        # Update final status
        completed_count = sum(1 for r in results if r.get("status") == "completed")
        failed_count = len(results) - completed_count
        final_status = "completed" if failed_count == 0 else "completed_with_errors"
        
        redis_client.update_job_field(UUID(job_id), "status", final_status)
        redis_client.update_job_field(UUID(job_id), "completed", completed_count)
        redis_client.update_job_field(UUID(job_id), "failed", failed_count)
        redis_client.update_job_field(UUID(job_id), "pending", 0)
        
        return {
            "job_id": job_id,
            "repository": repository_url,
            "branch": branch,
            "use_cases": use_cases,
            "status": final_status,
            "execution_method": "docker_pool",
            "total_use_cases": len(use_cases),
            "completed": completed_count,
            "failed": failed_count,
            "results": results,
            "message": f"Completed execution of {len(use_cases)} use cases using Docker pool"
        }
        
    except Exception as e:
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": str(datetime.now(timezone.utc))
        }
        redis_client.update_job_field(UUID(job_id), "status", "failed")
        redis_client.update_job_field(UUID(job_id), "error", str(e))
        redis_client.update_job_field(UUID(job_id), "error_details", error_info)
        self.update_state(state="FAILURE", meta={"error": str(e), "error_type": type(e).__name__})
        raise RuntimeError(str(e))
