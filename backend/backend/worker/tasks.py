import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
import json
from celery import Task
from git import Repo

from backend.worker.celery_app import celery_app
from backend.worker.config import WorkerConfig, config
from backend.worker.docker_runner import DockerRunner
from backend.worker.analysis_pipeline import AnalysisPipeline
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
    """Analyze a repository's documentation and extract use cases with parallel execution."""
    if include_folders is None:
        include_folders = ["docs"]
    
    redis_client = get_redis_client()
    
    try:
        # Update Redis with processing status
        redis_client.store_job_status(job_id, "PROCESSING", {
            "message": "Starting parallel analysis",
            "step": "parallel_setup"
        })
        
        # Update task state for Celery
        self.update_state(state="PROCESSING", meta={"status": "Starting parallel analysis"})
        
        # Create data directory structure: ../data/job_id/
        data_dir = os.path.join(WorkerConfig.DATA_DIR, job_id)
        repo_dir = os.path.join(data_dir, "repo")
        
        os.makedirs(data_dir, exist_ok=True)
        
        try:
            # Clone the repository
            repo = Repo.clone_from(repository_url, repo_dir, branch=branch)
            
            # Update Redis and task state
            redis_client.store_job_status(job_id, "PROCESSING", {
                "message": "Starting Docker analysis",
                "step": "docker_analysis"
            })
            self.update_state(state="PROCESSING", meta={"status": "Starting Docker analysis"})
            
            # Create Docker runner and execute analysis
            docker_runner = DockerRunner()
            
            # Run the complete analysis in Docker sandbox
            result = docker_runner.run_analysis(
                job_id=job_id,
                repo_path=repo_dir,
                include_folders=include_folders,
            )
            
            # Read the final results from the data directory
            results_path = os.path.join(data_dir, "data", "results.json")
            use_cases_path = os.path.join(data_dir, "data", "use_cases.json")
            
            # Read use cases
            use_cases = []
            if os.path.exists(use_cases_path):
                with open(use_cases_path) as f:
                    data = json.load(f)
                    use_cases = data.get("use_cases", [])
            
            # Use parallel execution for use cases
            from backend.worker.parallel_executor import UseCaseOrchestrator
            
            orchestrator = UseCaseOrchestrator(max_parallel=5)
            
            # Execute use cases in parallel
            parallel_result = orchestrator.execute_job_parallel(
                job_id=job_id,
                use_cases=use_cases,
                repo_path=repo_dir,
                output_dir=os.path.join(data_dir, "parallel_results"),
                include_folders=include_folders
            )
            
            # Store parallel execution results
            result = {
                "job_id": job_id,
                "repository": repository_url,
                "branch": branch,
                "use_cases": use_cases,
                "parallel_results": parallel_result,
                "status": "completed",
                "execution_method": "parallel",
                "max_parallel_containers": 5
            }
            
            redis_client.store_job_result(job_id, result)
            redis_client.store_job_status(job_id, "COMPLETED", {
                "message": "Parallel analysis completed successfully",
                "use_cases_count": len(use_cases),
                "parallel_summary": {
                    "completed": parallel_result["completed"],
                    "failed": parallel_result["failed"],
                    "total_containers": 5
                },
                "results_path": str(data_dir)
            })
            
            return result
            
        finally:
            # No need to cleanup - we keep the data directory for persistence
            pass
    except Exception as e:
        # Store error in Redis
        redis_client.store_job_status(job_id, "FAILED", {
            "error": str(e),
            "message": "Analysis failed"
        })
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise