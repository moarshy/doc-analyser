import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import docker
from docker.errors import DockerException

from .config import config


class DockerRunner:
    """Handles Docker container creation and execution for analysis tasks."""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException:
            self.client = None
            print("Warning: Docker not available. Using subprocess fallback.")
    
    def run_analysis(
        self,
        job_id: str,
        repo_path: str,
        include_folders: List[str],
    ) -> Dict[str, Any]:
        """Run the analysis pipeline in a Docker container."""
        
        # Create results directory
        results_dir = Path(config.VOLUME_PATH) / job_id
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy worker files to results directory
        worker_files = Path(__file__).parent
        shutil.copytree(worker_files, results_dir / "worker", dirs_exist_ok=True)
        
        # Mount volumes
        volumes = {
            str(Path(repo_path).resolve()): {"bind": "/workspace/repo", "mode": "ro"},
            str(results_dir.resolve()): {"bind": "/workspace/results", "mode": "rw"},
        }
        
        # Environment variables
        environment = {
            "JOB_ID": job_id,
            "REPO_PATH": "/workspace/repo",
            "RESULTS_PATH": "/workspace/results",
            "INCLUDE_FOLDERS": json.dumps(include_folders),
        }
        
        if self.client:
            return self._run_with_docker(volumes, environment)
        else:
            return self._run_with_subprocess(repo_path, str(results_dir), include_folders)
    
    def _run_with_docker(
        self,
        volumes: Dict[str, Dict[str, str]],
        environment: Dict[str, str],
    ) -> Dict[str, Any]:
        """Run analysis using Docker."""
        
        try:
            container = self.client.containers.run(
                image=config.DOCKER_IMAGE,
                command=["python", "/workspace/results/worker/analysis_pipeline.py"],
                volumes=volumes,
                environment=environment,
                working_dir="/workspace/results",
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                network=config.DOCKER_NETWORK,
                mem_limit="2g",
                cpu_quota=50000,  # 50% CPU limit
            )
            
            # Parse results
            results_path = Path(config.VOLUME_PATH) / os.environ.get("JOB_ID", "unknown") / "results.json"
            if results_path.exists():
                with open(results_path) as f:
                    return json.load(f)
            
            return {"status": "completed", "message": "Analysis completed"}
            
        except Exception as e:
            raise RuntimeError(f"Docker execution failed: {e}")
    
    def _run_with_subprocess(
        self,
        repo_path: str,
        results_path: str,
        include_folders: List[str],
    ) -> Dict[str, Any]:
        """Run analysis using subprocess as fallback."""
        
        try:
            # Set environment variables
            env = os.environ.copy()
            env.update({
                "JOB_ID": "subprocess",
                "REPO_PATH": repo_path,
                "RESULTS_PATH": results_path,
                "INCLUDE_FOLDERS": json.dumps(include_folders),
            })
            
            # Run the analysis script
            cmd = [
                "python",
                str(Path(__file__).parent / "analysis_pipeline.py"),
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=config.ANALYSIS_TIMEOUT,
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Analysis failed: {result.stderr}")
            
            # Try to parse results
            results_file = Path(results_path) / "results.json"
            if results_file.exists():
                with open(results_file) as f:
                    return json.load(f)
            
            return {"status": "completed", "stdout": result.stdout}
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Analysis timed out")
        except Exception as e:
            raise RuntimeError(f"Subprocess execution failed: {e}")
    
    def execute_use_case(
        self,
        job_id: str,
        use_case: Dict[str, Any],
        repo_path: str,
        include_folders: List[str],
    ) -> Dict[str, Any]:
        """Execute a specific use case in a container."""
        
        results_dir = Path(config.VOLUME_PATH) / job_id / "use_cases"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Create use case specific environment
        environment = {
            "JOB_ID": job_id,
            "USE_CASE": json.dumps(use_case),
            "REPO_PATH": "/workspace/repo",
            "RESULTS_PATH": "/workspace/results",
            "INCLUDE_FOLDERS": json.dumps(include_folders),
        }
        
        volumes = {
            str(Path(repo_path).resolve()): {"bind": "/workspace/repo", "mode": "ro"},
            str(results_dir.resolve()): {"bind": "/workspace/results", "mode": "rw"},
        }
        
        if self.client:
            container = self.client.containers.run(
                image=config.DOCKER_IMAGE,
                command=["python", "/workspace/results/worker/execute_use_case.py"],
                volumes=volumes,
                environment=environment,
                working_dir="/workspace/results",
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                mem_limit="1g",
                timeout=1800,  # 30 minutes
            )
            
            # Parse execution results
            use_case_result_file = results_dir / f"{use_case.get('name', 'unknown')}_results.json"
            if use_case_result_file.exists():
                with open(use_case_result_file) as f:
                    return json.load(f)
        
        return {"status": "completed", "use_case": use_case.get("name")}