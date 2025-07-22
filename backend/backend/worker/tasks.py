import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from uuid import UUID

from celery import Task
from git import Repo

from .celery_app import celery_app
from .config import WorkerConfig
from .docker_runner import DockerRunner
from .analysis_pipeline import AnalysisPipeline


class AnalysisTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        print(f"Task {task_id} failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        print(f"Task {task_id} completed successfully")
        super().on_success(retval, task_id, args, kwargs)


@celery_app.task(base=AnalysisTask, bind=True, name="analyze_repository")
def analyze_repository(
    self,
    job_id: str,
    repository_url: str,
    branch: str = "main",
    include_folders: List[str] = None,
) -> Dict[str, Any]:
    """Analyze a repository's documentation and extract use cases."""
    if include_folders is None:
        include_folders = ["docs"]
    
    try:
        # Update task state
        self.update_state(state="PROCESSING", meta={"status": "Cloning repository"})
        
        # Create temporary directory for the repository
        temp_dir = tempfile.mkdtemp(prefix=f"repo_{job_id}_")
        
        try:
            # Clone the repository
            repo = Repo.clone_from(repository_url, temp_dir, branch=branch)
            
            # Update task state
            self.update_state(state="PROCESSING", meta={"status": "Analyzing documentation"})
            
            # Create Docker runner
            docker_runner = DockerRunner()
            
            # Create analysis pipeline
            pipeline = AnalysisPipeline(
                job_id=job_id,
                repo_path=temp_dir,
                include_folders=include_folders,
                docker_runner=docker_runner,
            )
            
            # Run the analysis
            results = pipeline.run()
            
            return {
                "job_id": job_id,
                "repository": repository_url,
                "branch": branch,
                "use_cases": results.get("use_cases", []),
                "analysis_results": results.get("analysis_results", {}),
                "status": "completed",
            }
            
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise


@celery_app.task(base=AnalysisTask, bind=True, name="execute_use_case")
def execute_use_case(
    self,
    job_id: str,
    use_case: Dict[str, Any],
    repo_path: str,
    include_folders: List[str],
) -> Dict[str, Any]:
    """Execute a specific use case."""
    try:
        self.update_state(
            state="PROCESSING", 
            meta={"status": f"Executing use case: {use_case.get('name', 'Unknown')}"}
        )
        
        # Create Docker runner
        docker_runner = DockerRunner()
        
        # Execute the use case
        result = docker_runner.execute_use_case(
            job_id=job_id,
            use_case=use_case,
            repo_path=repo_path,
            include_folders=include_folders,
        )
        
        return {
            "job_id": job_id,
            "use_case": use_case.get("name"),
            "status": "completed",
            "result": result,
        }
        
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise