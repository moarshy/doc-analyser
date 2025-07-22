import json
import subprocess
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
        except DockerException as e:
            self.client = None
            print(f"Warning: Docker not available. Using subprocess fallback. Error: {e}")
    
    def _ensure_network_exists(self):
        """Ensure the Docker network exists, create if it doesn't."""
        try:
            networks = self.client.networks.list(names=[config.DOCKER_NETWORK])
            if not networks:
                self.client.networks.create(config.DOCKER_NETWORK, driver="bridge")
                print(f"Created Docker network: {config.DOCKER_NETWORK}")
        except Exception as e:
            print(f"Warning: Could not create Docker network: {e}")
    
    def extract_use_cases(
        self,
        job_id: str,
        repo_path: str,
        include_folders: List[str],
        output_dir: str
    ) -> Dict[str, Any]:
        """Extract use cases from repository documentation using Docker."""
        
        try:
            job_dir = Path(config.DATA_DIR) / job_id
            repo_dir = Path(repo_path)
            data_dir = Path(output_dir)
            
            job_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Mount volumes
            volumes = {
                str(repo_dir.resolve()): {"bind": "/workspace/repo", "mode": "ro"},
                str(data_dir.resolve()): {"bind": "/workspace/data", "mode": "rw"},
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
                self.client.containers.run(
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
                
                return {"status": "completed", "message": "Use cases extracted successfully"}
            else:
                return self._run_extraction_fallback(repo_path, str(data_dir), include_folders)
                
        except Exception as e:
            raise RuntimeError(f"Use case extraction failed: {e}")

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
        
        try:
            job_dir = Path(config.DATA_DIR) / job_id
            repo_dir = Path(repo_path)
            data_dir = Path(output_dir)
            
            job_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Mount volumes
            volumes = {
                str(repo_dir.resolve()): {"bind": "/workspace/repo", "mode": "ro"},
                str(data_dir.resolve()): {"bind": "/workspace/data", "mode": "rw"},
            }
            
            # Environment variables
            environment = {
                "JOB_ID": job_id,
                "USE_CASE_INDEX": str(use_case_index),
                "REPO_PATH": "/workspace/repo",
                "DATA_PATH": "/workspace/data",
                "INCLUDE_FOLDERS": json.dumps(include_folders),
                "ANTHROPIC_AUTH_TOKEN": config.ANTHROPIC_AUTH_TOKEN,
                "ANTHROPIC_BASE_URL": config.ANTHROPIC_BASE_URL,
            }
            
            if self.client:
                try:
                    container = self.client.containers.run(
                        image=config.DOCKER_SANDBOX_IMAGE,
                        command=[
                            "python", "/workspace/execute_use_case.py",
                            "/workspace/data/use_cases.json",
                            "/workspace/data",
                            ",".join(include_folders),
                            str(use_case_index)
                        ],
                        volumes=volumes,
                        environment=environment,
                        working_dir="/workspace",
                        remove=True,
                        detach=False,
                        stdout=True,
                        stderr=True,
                        network=config.DOCKER_NETWORK,
                        mem_limit="1g",
                        cpu_quota=20000,
                    )
                    
                    # container is a bytes object when detach=False
                    stdout = container.decode('utf-8') if isinstance(container, bytes) else str(container)
                    
                    return {
                        "status": "completed",
                        "exit_code": 0,
                        "container_id": job_id,
                        "stdout": stdout,
                        "message": f"Use case {use_case_index} executed successfully"
                    }
                except Exception as e:
                    return {
                        "status": "failed",
                        "exit_code": 1,
                        "error": str(e),
                        "stderr": str(e)
                    }
            else:
                return self._run_execution_fallback(use_case_index, repo_path, str(data_dir), include_folders)
                
        except Exception as e:
            return {
                "status": "failed",
                "exit_code": 1,
                "error": str(e)
            }

    def _run_extraction_fallback(self, repo_path: str, data_dir: str, include_folders: List[str]) -> Dict[str, Any]:
        """Fallback for extraction using subprocess."""
        try:
            import subprocess
            import os
            
            env = os.environ.copy()
            env.update({
                "JOB_ID": "subprocess",
                "REPO_PATH": repo_path,
                "DATA_PATH": data_dir,
                "INCLUDE_FOLDERS": json.dumps(include_folders),
                "ANTHROPIC_AUTH_TOKEN": config.ANTHROPIC_AUTH_TOKEN,
                "ANTHROPIC_BASE_URL": config.ANTHROPIC_BASE_URL,
            })
            
            cmd = [
                "python",
                str(Path(__file__).parent / "use_case.py"),
                repo_path,
                data_dir
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}