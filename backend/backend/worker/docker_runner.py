import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import docker
from docker.errors import DockerException

from backend.worker.config import config


class DockerRunner:
    """Handles Docker container creation and execution for analysis tasks."""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
            self._ensure_network_exists()
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
        
        job_dir = Path(config.DATA_DIR) / job_id
        repo_dir = job_dir / "repo"
        data_dir = job_dir / "data"
        
        job_dir.mkdir(parents=True, exist_ok=True)
        repo_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mount volumes
        volumes = {
            str(Path(repo_path).resolve()): {"bind": "/workspace/repo", "mode": "ro"},
            str(job_dir.resolve()): {"bind": "/workspace/data", "mode": "rw"},
        }
        
        # Environment variables
        environment = {
            "JOB_ID": job_id,
            "REPO_PATH": "/workspace/repo",
            "DATA_PATH": "/workspace/data",
            "INCLUDE_FOLDERS": json.dumps(include_folders),
            "ANTHROPIC_AUTH_TOKEN": config.ANTHROPIC_AUTH_TOKEN,
            "ANTHROPIC_BASE_URL": config.ANTHROPIC_BASE_URL,
        }
        
        if self.client:
            return self._run_with_docker_sandbox(volumes, environment, job_id)
        else:
            return self._run_with_subprocess(repo_path, str(data_dir), include_folders)
    
    def _run_with_docker_sandbox(
        self,
        volumes: Dict[str, Dict[str, str]],
        environment: Dict[str, str],
        job_id: str,
    ) -> Dict[str, Any]:
        """Run analysis using Claude Code sandbox Docker image with parallel execution."""
        
        try:
            # Step 1: Run use case extraction (single container)
            container1 = self.client.containers.run(
                image=config.DOCKER_SANDBOX_IMAGE,
                command=["python", "/workspace/use_case.py", "/workspace/repo", "/workspace/data"],
                volumes=volumes,
                environment=environment,
                working_dir="/workspace",
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                network=config.DOCKER_NETWORK,
                mem_limit="2g",
                cpu_quota=50000,
            )
            
            # Step 2: Read use cases and run parallel execution
            job_dir = Path(config.DATA_DIR) / job_id
            use_cases_path = job_dir / "use_cases.json"
            
            if not use_cases_path.exists():
                return {"status": "completed", "job_id": job_id, "message": "No use cases found"}
            
            with open(use_cases_path) as f:
                use_cases_data = json.load(f)
            
            use_cases = use_cases_data.get("use_cases", [])
            
            if not use_cases:
                return {"status": "completed", "job_id": job_id, "message": "No use cases to execute"}
            
            # Import parallel executor
            from backend.worker.parallel_executor import UseCaseOrchestrator
            
            # Create output directory for parallel results
            parallel_output_dir = job_dir / "parallel_results"
            parallel_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Run parallel execution
            orchestrator = UseCaseOrchestrator(max_parallel=5)
            
            # Since DockerRunner runs synchronously, we need to run the async orchestrator
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                repo_path_str = str(next(iter(volumes.keys())))
                parallel_result = loop.run_until_complete(
                    orchestrator.execute_job_parallel(
                        job_id=job_id,
                        use_cases=use_cases,
                        repo_path=repo_path_str,
                        output_dir=str(parallel_output_dir),
                        include_folders=json.loads(environment["INCLUDE_FOLDERS"])
                    )
                )
            finally:
                loop.close()
            
            # Store parallel results
            results_summary = {
                "status": "completed",
                "job_id": job_id,
                "use_cases": use_cases,
                "parallel_results": parallel_result,
                "message": "Analysis completed successfully with parallel execution",
                "execution_method": "parallel",
                "max_parallel_containers": 5
            }
            
            # Save results to file
            results_file = job_dir / "data" / "results.json"
            with open(results_file, 'w') as f:
                json.dump(results_summary, f, indent=2)
            
            return results_summary
            
        except Exception as e:
            raise RuntimeError(f"Docker execution failed: {e}")
    
    def _ensure_network_exists(self):
        """Ensure the Docker network exists, create if it doesn't."""
        try:
            networks = self.client.networks.list(names=[config.DOCKER_NETWORK])
            if not networks:
                self.client.networks.create(config.DOCKER_NETWORK, driver="bridge")
                print(f"Created Docker network: {config.DOCKER_NETWORK}")
        except Exception as e:
            print(f"Warning: Could not create Docker network: {e}")
    
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