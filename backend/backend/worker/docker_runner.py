import json
import subprocess
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from uuid import UUID

import docker
from docker.errors import DockerException

from backend.worker.config import config

logger = logging.getLogger("backend.worker.docker_runner")


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

    def execute_use_cases_with_pool(
        self,
        job_id: str,
        use_cases: List[Dict[str, Any]],
        repo_path: str,
        output_dir: str,
        include_folders: List[str],
        pool_size: int = 5,
        redis_client=None,
        task_context=None
    ) -> List[Dict[str, Any]]:
        """Execute use cases using a pool of Docker containers with polling."""
        
        if not self.client:
            raise RuntimeError("Docker not available - cannot use container pool")
        
        total_use_cases = len(use_cases)
        logger.info(f"🚀 Starting Docker pool execution: {total_use_cases} use cases, pool size: {pool_size}")
        
        results = []
        use_case_queue = list(enumerate(use_cases))  # [(index, use_case), ...]
        completed_count = 0
        failed_count = 0
        
        # Container pool: {container_id: {status, use_case_index, container_obj}}
        container_pool = {}
        
        try:
            job_dir = Path(config.DATA_DIR) / job_id
            repo_dir = Path(repo_path)
            data_dir = Path(output_dir)
            
            # Mount volumes
            volumes = {
                str(repo_dir.resolve()): {"bind": "/workspace/repo", "mode": "ro"},
                str(data_dir.resolve()): {"bind": "/workspace/data", "mode": "rw"},
            }
            
            # Start initial containers (up to pool_size)
            initial_batch = min(pool_size, len(use_case_queue))
            logger.info(f"🏗️ Starting initial batch of {initial_batch} containers...")
            
            for i in range(initial_batch):
                use_case_index, use_case = use_case_queue.pop(0)
                use_case_name = use_case.get('name', f'Use Case {use_case_index}')
                
                logger.info(f"📦 Starting container for use case {use_case_index}: {use_case_name}")
                container_id = self._start_use_case_container(
                    job_id, use_case_index, use_case, volumes, include_folders
                )
                if container_id:
                    container_pool[container_id] = {
                        "status": "running",
                        "use_case_index": use_case_index,
                        "container_obj": self.client.containers.get(container_id),
                        "start_time": time.time(),
                        "use_case_name": use_case_name
                    }
                    
                    # Update Redis status with start time
                    if redis_client:
                        self._update_use_case_status(redis_client, job_id, use_case_index, "running", 
                                                   start_time=time.time())
                    
                    logger.info(f"✅ Container {container_id[:12]} started for use case {use_case_index}")
                else:
                    logger.error(f"❌ Failed to start container for use case {use_case_index}")
            
            logger.info(f"🔄 Starting polling loop - {len(container_pool)} containers running, {len(use_case_queue)} queued")
            
            # Polling loop
            poll_count = 0
            while container_pool or use_case_queue:
                poll_count += 1
                
                # Log progress every poll
                progress_msg = f"📊 Poll #{poll_count} - Progress: {completed_count + failed_count}/{total_use_cases} completed ({completed_count} ✅, {failed_count} ❌), {len(container_pool)} running, {len(use_case_queue)} queued"
                logger.info(progress_msg)
                
                if task_context:
                    task_context.update_state(
                        state="PROCESSING", 
                        meta={
                            "status": f"Executing use cases: {completed_count + failed_count}/{total_use_cases} completed",
                            "completed": completed_count,
                            "failed": failed_count,
                            "running": len(container_pool),
                            "queued": len(use_case_queue),
                            "poll_count": poll_count
                        }
                    )
                
                # Check container statuses
                completed_containers = []
                
                for container_id, container_info in container_pool.items():
                    container = container_info["container_obj"]
                    
                    try:
                        container.reload()
                        if container.status in ["exited", "dead"]:
                            # Container finished
                            use_case_index = container_info["use_case_index"]
                            use_case_name = container_info["use_case_name"]
                            execution_time = time.time() - container_info["start_time"]
                            
                            result = self._collect_container_result(container, use_case_index, container_info["start_time"])
                            results.append(result)
                            
                            if result["status"] == "completed":
                                completed_count += 1
                                logger.info(f"✅ Use case {use_case_index} completed successfully in {execution_time:.1f}s: {use_case_name}")
                                if redis_client:
                                    self._update_use_case_status(redis_client, job_id, use_case_index, "completed",
                                                               end_time=time.time(), 
                                                               execution_time=execution_time,
                                                               container_logs=result.get("stdout", ""),
                                                               container_id=result.get("container_id", ""))
                            else:
                                failed_count += 1
                                logger.error(f"❌ Use case {use_case_index} failed after {execution_time:.1f}s: {use_case_name}")
                                if redis_client:
                                    self._update_use_case_status(redis_client, job_id, use_case_index, "failed",
                                                               end_time=time.time(),
                                                               execution_time=execution_time,
                                                               container_logs=result.get("stdout", ""),
                                                               error_details=result.get("error", ""),
                                                               container_id=result.get("container_id", ""))
                            
                            completed_containers.append(container_id)
                            
                            # Clean up container
                            try:
                                container.remove()
                                logger.debug(f"🧹 Cleaned up container {container_id[:12]}")
                            except:
                                pass
                            
                    except Exception as e:
                        # Container error
                        use_case_index = container_info["use_case_index"]
                        use_case_name = container_info["use_case_name"]
                        execution_time = time.time() - container_info["start_time"]
                        
                        logger.error(f"💥 Container error for use case {use_case_index} after {execution_time:.1f}s: {use_case_name} - {str(e)}")
                        
                        results.append({
                            "use_case_index": use_case_index,
                            "status": "failed",
                            "error": str(e),
                            "execution_time": execution_time
                        })
                        failed_count += 1
                        completed_containers.append(container_id)
                        
                        if redis_client:
                            self._update_use_case_status(redis_client, job_id, use_case_index, "failed",
                                                       end_time=time.time(),
                                                       execution_time=execution_time,
                                                       error_details=str(e))
                
                # Remove completed containers from pool
                for container_id in completed_containers:
                    del container_pool[container_id]
                
                # Start new containers for remaining use cases
                while len(container_pool) < pool_size and use_case_queue:
                    use_case_index, use_case = use_case_queue.pop(0)
                    use_case_name = use_case.get('name', f'Use Case {use_case_index}')
                    
                    logger.info(f"🔄 Starting next container for use case {use_case_index}: {use_case_name}")
                    container_id = self._start_use_case_container(
                        job_id, use_case_index, use_case, volumes, include_folders
                    )
                    if container_id:
                        container_pool[container_id] = {
                            "status": "running",
                            "use_case_index": use_case_index,
                            "container_obj": self.client.containers.get(container_id),
                            "start_time": time.time(),
                            "use_case_name": use_case_name
                        }
                        
                        if redis_client:
                            self._update_use_case_status(redis_client, job_id, use_case_index, "running",
                                                       start_time=time.time())
                        
                        logger.info(f"✅ Container {container_id[:12]} started for use case {use_case_index}")
                    else:
                        logger.error(f"❌ Failed to start container for use case {use_case_index}")
                
                # Wait before next poll
                if container_pool:  # Only sleep if there are running containers
                    logger.debug(f"⏳ Waiting 10s before next poll...")
                    time.sleep(10)  # Poll every 10 seconds
            
            # Final summary
            logger.info(f"🎉 Docker pool execution completed! Total: {total_use_cases}, Completed: {completed_count} ✅, Failed: {failed_count} ❌")
            
            # Sort results by use_case_index
            results.sort(key=lambda x: x.get("use_case_index", 0))
            return results
            
        except Exception as e:
            # Clean up any remaining containers
            logger.error(f"💥 Docker pool execution failed: {e}")
            logger.info(f"🧹 Cleaning up {len(container_pool)} remaining containers...")
            
            for container_info in container_pool.values():
                try:
                    container_info["container_obj"].remove(force=True)
                    logger.debug(f"🧹 Forced cleanup of container {container_info['container_obj'].id[:12]}")
                except:
                    pass
            raise RuntimeError(f"Docker pool execution failed: {e}")
    
    def _start_use_case_container(
        self, 
        job_id: str, 
        use_case_index: int, 
        use_case: Dict[str, Any], 
        volumes: Dict, 
        include_folders: List[str]
    ) -> str:
        """Start a container for a single use case and return container ID."""
        
        environment = {
            "JOB_ID": job_id,
            "USE_CASE_INDEX": str(use_case_index),
            "REPO_PATH": "/workspace/repo",
            "DATA_PATH": "/workspace/data",
            "INCLUDE_FOLDERS": json.dumps(include_folders),
            "ANTHROPIC_AUTH_TOKEN": config.ANTHROPIC_AUTH_TOKEN,
            "ANTHROPIC_BASE_URL": config.ANTHROPIC_BASE_URL,
        }
        
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
                detach=True,  # Run in background
                network=config.DOCKER_NETWORK,
                mem_limit="1g",
                cpu_quota=20000,
            )
            return container.id
        except Exception as e:
            print(f"Failed to start container for use case {use_case_index}: {e}")
            return None
    
    def _collect_container_result(self, container, use_case_index: int, start_time: float) -> Dict[str, Any]:
        """Collect results from a completed container."""
        
        try:
            exit_code = container.attrs["State"]["ExitCode"]
            logs = container.logs().decode('utf-8')
            
            return {
                "use_case_index": use_case_index,
                "status": "completed" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "container_id": container.id[:12],
                "stdout": logs,
                "execution_time": time.time() - start_time,
                "message": f"Use case {use_case_index} {'completed' if exit_code == 0 else 'failed'}"
            }
        except Exception as e:
            return {
                "use_case_index": use_case_index,
                "status": "failed",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def _update_use_case_status(self, redis_client, job_id: str, use_case_index: int, status: str, 
                              start_time=None, end_time=None, execution_time=None, 
                              container_logs=None, error_details=None, container_id=None):
        """Update use case status in Redis with timing and execution details."""
        try:
            job_data = redis_client.get_job(UUID(job_id))
            if job_data and "use_cases" in job_data:
                use_cases = job_data["use_cases"]
                if str(use_case_index) in use_cases:
                    use_case = use_cases[str(use_case_index)]
                    use_case["status"] = status
                    
                    # Add timing information
                    if start_time is not None:
                        use_case["start_time"] = start_time
                        use_case["start_time_iso"] = datetime.fromtimestamp(start_time, timezone.utc).isoformat()
                    
                    if end_time is not None:
                        use_case["end_time"] = end_time
                        use_case["end_time_iso"] = datetime.fromtimestamp(end_time, timezone.utc).isoformat()
                    
                    if execution_time is not None:
                        use_case["execution_time_seconds"] = execution_time
                    
                    # Add execution details
                    if container_logs is not None:
                        use_case["container_logs"] = container_logs
                    
                    if error_details is not None:
                        use_case["error_details"] = error_details
                    
                    if container_id is not None:
                        use_case["container_id"] = container_id
                    
                    # Update last modified timestamp
                    use_case["updated_at"] = datetime.now(timezone.utc).isoformat()
                    
                    # Store updated use cases
                    redis_client.update_job_field(UUID(job_id), "use_cases", use_cases)
                    
        except Exception as e:
            logger.error(f"Failed to update Redis status for use case {use_case_index}: {e}")