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


@celery_app.task(base=AnalysisTask, bind=True, name="analyze_repository")
def analyze_repository(
    self,
    job_id: str,
    repository_url: str,
    branch: str = "main",
    include_folders: List[str] = None,
) -> Dict[str, Any]:
    """Extract use cases from repository documentation."""
    if include_folders is None:
        include_folders = ["docs"]
    
    redis_client = get_redis_client()
    
    try:
        # Initialize job directories with correct structure
        data_dir = os.path.join(WorkerConfig.DATA_DIR, job_id)
        repo_dir = os.path.join(data_dir, "repo")
        output_dir = os.path.join(data_dir, "data")  # All output files here
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(repo_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        # Update job with paths and status
        redis_client.update_job_field(UUID(job_id), "repo_path", repo_dir)
        redis_client.update_job_field(UUID(job_id), "data_path", output_dir)
        redis_client.update_job_field(UUID(job_id), "status", "extracting")
        self.update_state(state="PROCESSING", meta={"status": "Extracting use cases"})
        
        # Clone repository
        repo = Repo.clone_from(repository_url, repo_dir, branch=branch)
        
        # Extract use cases using Docker
        docker_runner = DockerRunner()
        try:
            extraction_result = docker_runner.extract_use_cases(
                job_id=job_id,
                repo_path=repo_dir,
                include_folders=include_folders,
                output_dir=output_dir  # All files go to data_path/job_id/data/
            )
            
            # Read extracted use cases
            use_cases_path = os.path.join(output_dir, "use_cases.json")
            use_cases = []
            if os.path.exists(use_cases_path):
                with open(use_cases_path) as f:
                    data = json.load(f)
                    use_cases = data.get("use_cases", [])
            else:
                # Check for error logs
                error_log_path = os.path.join(data_dir, "data", "extraction_error.log")
                if os.path.exists(error_log_path):
                    with open(error_log_path) as f:
                        error_content = f.read()
                        raise RuntimeError(f"Use case extraction failed: {error_content}")
                
                use_cases = []  # Default empty list if no file
                
        except Exception as e:
            # Capture detailed error information
            error_details = {
                "error": str(e),
                "error_type": type(e).__name__,
                "repo_path": repo_dir,
                "include_folders": include_folders,
                "data_path": output_dir
            }
            tasks_logger.error(f"Use case extraction failed: {error_details}")
            redis_client.update_job_field(UUID(job_id), "status", "failed")
            redis_client.update_job_field(UUID(job_id), "error", str(e))
            redis_client.update_job_field(UUID(job_id), "error_details", error_details)
            raise RuntimeError(str(e))
        
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
            job_data["status"] = "queued"
            redis_client.store_job(UUID(job_id), job_data)
        
        # Queue individual use case execution tasks
        for i, use_case in enumerate(use_cases):
            execute_single_use_case.delay(
                job_id=job_id,  # Keep as string for consistency
                use_case_index=i,
                use_case=use_case,
                repo_path=repo_dir,
                output_dir=output_dir,  # All files go to data_path/job_id/data/
                include_folders=include_folders
            )
        
        return {
            "job_id": job_id,
            "repository": repository_url,
            "branch": branch,
            "use_cases": use_cases,
            "status": "queued",
            "execution_method": "parallel_celery",
            "total_use_cases": len(use_cases),
            "message": f"Queued {len(use_cases)} use cases for parallel execution"
        }
        
    except Exception as e:
        # Capture detailed error information for proper serialization
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


@celery_app.task(base=AnalysisTask, bind=True, name="execute_single_use_case")
def execute_single_use_case(
    self,
    job_id: str,
    use_case_index: int,
    use_case: Dict[str, Any],
    repo_path: str,
    output_dir: str,
    include_folders: List[str],
) -> Dict[str, Any]:
    """Execute a single use case in a Docker container."""
    
    redis_client = get_redis_client()
    
    try:
        # Update Redis status
        job_data = redis_client.get_job(UUID(job_id)) or {}
        use_cases = job_data.get("use_cases", {})
        
        if str(use_case_index) in use_cases:
            use_cases[str(use_case_index)]["status"] = "running"
            redis_client.update_job_field(UUID(job_id), "use_cases", use_cases)
        
        self.update_state(state="PROCESSING", meta={
            "use_case_index": use_case_index,
            "use_case_name": use_case.get("name", f"Use Case {use_case_index}")
        })
        
        # Execute use case in Docker
        docker_runner = DockerRunner()
        result = docker_runner.execute_single_use_case(
            job_id=job_id,
            use_case_index=use_case_index,
            use_case=use_case,
            repo_path=repo_path,
            output_dir=output_dir,
            include_folders=include_folders
        )
        
        # Update Redis with result
        job_data = redis_client.get_job(UUID(job_id)) or {}
        use_cases = job_data.get("use_cases", {})
        
        if str(use_case_index) in use_cases:
            use_cases[str(use_case_index)].update({
                "status": "completed" if result["exit_code"] == 0 else "failed",
                "result": result,
                "completed_at": str(datetime.now(timezone.utc))
            })
            
            # Update counters
            job_data["use_cases"] = use_cases
            completed = sum(1 for uc in use_cases.values() if uc.get("status") == "completed")
            failed = sum(1 for uc in use_cases.values() if uc.get("status") == "failed")
            
            job_data.update({
                "completed": completed,
                "failed": failed,
                "pending": job_data.get("total_use_cases", 0) - completed - failed
            })
            
            if job_data.get("pending", 0) == 0:
                job_data["status"] = "completed"
            
            redis_client.store_job(UUID(job_id), job_data)
        
        return {
            "job_id": job_id,
            "use_case_index": use_case_index,
            "use_case_name": use_case.get("name"),
            "status": "completed" if result["exit_code"] == 0 else "failed",
            "result": result
        }
        
    except Exception as e:
        # Update Redis with error using proper serialization
        error_info = {
            "error": str(e),
            "error_type": type(e).__name__,
            "timestamp": str(datetime.now(timezone.utc))
        }
        
        job_data = redis_client.get_job(UUID(job_id)) or {}
        use_cases = job_data.get("use_cases", {})
        
        if str(use_case_index) in use_cases:
            use_cases[str(use_case_index)].update({
                "status": "failed",
                "error": str(e),
                "error_details": error_info
            })
            job_data["use_cases"] = use_cases
            job_data["failed"] = job_data.get("failed", 0) + 1
            job_data["pending"] = max(0, job_data.get("pending", 0) - 1)
            job_data["status"] = "completed" if job_data.get("pending", 0) == 0 else "processing"
            redis_client.store_job(UUID(job_id), job_data)
        
        self.update_state(state="FAILURE", meta={
            "use_case_index": use_case_index,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise RuntimeError(str(e))