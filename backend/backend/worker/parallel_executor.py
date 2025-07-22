"""
Parallel Docker execution system for use cases.
Manages 5 concurrent Docker containers with Redis-based orchestration.
"""
import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4

import docker
from docker.models.containers import Container

from backend.common.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class ParallelDockerExecutor:
    """Manages parallel execution of use cases using Docker containers."""
    
    def __init__(self, max_containers: int = 5, redis_url: str = None):
        self.max_containers = max_containers
        self.redis = get_redis_client(redis_url)
        self.docker_client = docker.from_env()
        self.active_containers: Dict[str, Container] = {}
        self.container_pool: List[str] = []
        
        # Key prefixes for parallel execution
        self.QUEUE_PREFIX = "parallel:queue"
        self.CONTAINER_PREFIX = "parallel:container"
        self.LOG_PREFIX = "parallel:log"
        self.RESULT_PREFIX = "parallel:result"
        
    def add_use_cases_to_queue(self, job_id: str, use_cases: List[Dict[str, Any]]) -> int:
        """Add use cases to the parallel execution queue.
        
        Args:
            job_id: Parent analysis job ID
            use_cases: List of use cases to execute
            
        Returns:
            Number of use cases added to queue
        """
        queue_key = f"{self.QUEUE_PREFIX}:{job_id}"
        
        # Prepare queue items
        queue_items = []
        for i, use_case in enumerate(use_cases):
            item = {
                "id": str(uuid4()),
                "job_id": job_id,
                "use_case": use_case,
                "index": i,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            queue_items.append(item)
        
        # Store in Redis
        self.redis.client.lpush(queue_key, *[json.dumps(item) for item in queue_items])
        self.redis.client.expire(queue_key, 86400)  # 24 hours TTL
        
        logger.info(f"Added {len(queue_items)} use cases to queue for job {job_id}")
        return len(queue_items)
    
    def get_next_use_case(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the next pending use case from queue.
        
        Args:
            job_id: Parent analysis job ID
            
        Returns:
            Next use case or None if queue is empty
        """
        queue_key = f"{self.QUEUE_PREFIX}:{job_id}"
        
        # Get next item from queue (right pop = FIFO)
        item_data = self.redis.client.rpop(queue_key)
        if not item_data:
            return None
        
        return json.loads(item_data)
    
    def update_use_case_status(self, use_case_id: str, job_id: str, status: str, 
                              metadata: Dict[str, Any] = None) -> bool:
        """Update use case execution status.
        
        Args:
            use_case_id: Use case execution ID
            job_id: Parent job ID
            status: Current status
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        key = f"{self.RESULT_PREFIX}:{job_id}:{use_case_id}"
        data = {
            "use_case_id": use_case_id,
            "job_id": job_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **(metadata or {})
        }
        
        self.redis.client.setex(key, 86400, json.dumps(data, default=str))
        return True
    
    def start_container(self, container_id: str, job_id: str, use_case: Dict[str, Any],
                       repo_path: str, output_dir: str, include_folders: List[str]) -> Container:
        """Start a Docker container for use case execution.
        
        Args:
            container_id: Unique container identifier
            job_id: Parent analysis job ID
            use_case: Use case to execute
            repo_path: Repository path
            output_dir: Output directory
            include_folders: Folders to include
            
        Returns:
            Docker container instance
        """
        try:
            # Create container-specific output directory
            container_output = Path(output_dir) / f"container_{container_id}"
            container_output.mkdir(parents=True, exist_ok=True)
            
            # Prepare use case data
            use_case_file = container_output / "use_case.json"
            with open(use_case_file, 'w') as f:
                json.dump(use_case, f, indent=2)
            
            # Environment variables
            environment = {
                "JOB_ID": job_id,
                "CONTAINER_ID": container_id,
                "USE_CASE_PATH": str(use_case_file),
                "REPO_PATH": "/workspace/repo",
                "OUTPUT_PATH": str(container_output),
                "INCLUDE_FOLDERS": json.dumps(include_folders),
            }
            
            # Volumes
            volumes = {
                str(Path(repo_path).resolve()): {"bind": "/workspace/repo", "mode": "ro"},
                str(container_output.resolve()): {"bind": "/workspace/data", "mode": "rw"},
            }
            
            # Start container with specific use case ID
            container = self.docker_client.containers.run(
                image="doc-analyser-sandbox:latest",
                command=[
                    "python", "/workspace/execute_use_case.py",
                    "/workspace/data/use_cases.json",  # Original use cases file
                    "/workspace/data",
                    ",".join(include_folders),
                    str(use_case.get("index", 0))  # Use case ID for individual execution
                ],
                volumes=volumes,
                environment=environment,
                working_dir="/workspace",
                detach=True,
                remove=True,
                mem_limit="1g",
                cpu_quota=20000,
                name=f"use_case_executor_{container_id}_{int(time.time())}"
            )
            
            # Store container info
            container_key = f"{self.CONTAINER_PREFIX}:{container_id}"
            container_info = {
                "container_id": container.id,
                "job_id": job_id,
                "use_case_id": use_case.get("id"),
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "logs": []
            }
            self.redis.client.setex(container_key, 86400, json.dumps(container_info))
            
            self.active_containers[container_id] = container
            logger.info(f"Started container {container_id} for use case {use_case.get('id')}")
            
            return container
            
        except Exception as e:
            logger.error(f"Failed to start container {container_id}: {e}")
            raise
    
    def capture_container_logs(self, container: Container, container_id: str, job_id: str) -> str:
        """Capture logs from a running container.
        
        Args:
            container: Docker container
            container_id: Container identifier
            job_id: Parent job ID
            
        Returns:
            Complete log output
        """
        try:
            # Get logs with timestamps
            logs = container.logs(stdout=True, stderr=True, timestamps=True, follow=False)
            log_str = logs.decode('utf-8') if logs else ""
            
            # Store logs in Redis
            log_key = f"{self.LOG_PREFIX}:{job_id}:{container_id}"
            self.redis.client.setex(log_key, 86400, log_str)
            
            # Update container info with logs
            container_key = f"{self.CONTAINER_PREFIX}:{container_id}"
            container_info = json.loads(self.redis.client.get(container_key) or "{}")
            container_info["logs"] = log_str
            container_info["logs_captured_at"] = datetime.now(timezone.utc).isoformat()
            self.redis.client.setex(container_key, 86400, json.dumps(container_info))
            
            return log_str
            
        except Exception as e:
            logger.error(f"Failed to capture logs from container {container_id}: {e}")
            return f"Error capturing logs: {e}"
    
    def wait_for_container_completion(self, container: Container, container_id: str, 
                                    job_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for container completion and capture results.
        
        Args:
            container: Docker container
            container_id: Container identifier
            job_id: Parent job ID
            timeout: Timeout in seconds
            
        Returns:
            Container execution results
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                container.reload()
                
                if container.status == "exited":
                    # Capture final logs
                    logs = self.capture_container_logs(container, container_id, job_id)
                    
                    # Check exit code
                    exit_code = container.attrs.get('State', {}).get('ExitCode', -1)
                    
                    # Update container status
                    container_key = f"{self.CONTAINER_PREFIX}:{container_id}"
                    container_info = json.loads(self.redis.client.get(container_key) or "{}")
                    container_info.update({
                        "status": "completed" if exit_code == 0 else "failed",
                        "exit_code": exit_code,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    })
                    self.redis.client.setex(container_key, 86400, json.dumps(container_info))
                    
                    # Cleanup container
                    try:
                        container.remove(force=True)
                    except:
                        pass
                    
                    self.active_containers.pop(container_id, None)
                    
                    return {
                        "container_id": container_id,
                        "exit_code": exit_code,
                        "logs": logs,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                
                time.sleep(2)
            
            # Timeout
            logger.warning(f"Container {container_id} timed out after {timeout}s")
            self.capture_container_logs(container, container_id, job_id)
            
            try:
                container.kill()
            except:
                pass
            
            return {
                "container_id": container_id,
                "exit_code": -1,
                "error": "timeout",
                "logs": self.capture_container_logs(container, container_id, job_id)
            }
            
        except Exception as e:
            logger.error(f"Error waiting for container {container_id}: {e}")
            return {
                "container_id": container_id,
                "exit_code": -1,
                "error": str(e)
            }
    
    def get_available_containers(self) -> int:
        """Get number of available container slots."""
        running_containers = len(self.active_containers)
        return max(0, self.max_containers - running_containers)
    
    def get_container_status(self, job_id: str) -> Dict[str, Any]:
        """Get current status of all containers for a job."""
        container_pattern = f"{self.CONTAINER_PREFIX}:*"
        container_keys = self.redis.client.keys(container_pattern)
        
        status = {
            "total_containers": 0,
            "running_containers": 0,
            "completed_containers": 0,
            "failed_containers": 0,
            "containers": []
        }
        
        for key in container_keys:
            container_data = self.redis.client.get(key)
            if container_data:
                container_info = json.loads(container_data)
                if container_info.get("job_id") == job_id:
                    status["containers"].append(container_info)
                    status["total_containers"] += 1
                    
                    container_status = container_info.get("status", "unknown")
                    if container_status == "running":
                        status["running_containers"] += 1
                    elif container_status == "completed":
                        status["completed_containers"] += 1
                    elif container_status == "failed":
                        status["failed_containers"] += 1
        
        return status
    
    def get_job_results(self, job_id: str) -> Dict[str, Any]:
        """Get all results for a job."""
        result_pattern = f"{self.RESULT_PREFIX}:{job_id}:*"
        result_keys = self.redis.client.keys(result_pattern)
        
        results = {}
        for key in result_keys:
            use_case_id = key.replace(f"{self.RESULT_PREFIX}:{job_id}:", "")
            result_data = self.redis.client.get(key)
            if result_data:
                results[use_case_id] = json.loads(result_data)
        
        return results
    
    def get_job_logs(self, job_id: str) -> Dict[str, str]:
        """Get all logs for a job."""
        log_pattern = f"{self.LOG_PREFIX}:{job_id}:*"
        log_keys = self.redis.client.keys(log_pattern)
        
        logs = {}
        for key in log_keys:
            container_id = key.replace(f"{self.LOG_PREFIX}:{job_id}:", "")
            log_data = self.redis.client.get(key)
            if log_data:
                logs[container_id] = log_data
        
        return logs
    
    def cleanup_job_data(self, job_id: str) -> bool:
        """Clean up all data for a specific job."""
        try:
            patterns = [
                f"{self.QUEUE_PREFIX}:{job_id}",
                f"{self.CONTAINER_PREFIX}:*",
                f"{self.LOG_PREFIX}:{job_id}:*",
                f"{self.RESULT_PREFIX}:{job_id}:*"
            ]
            
            for pattern in patterns:
                keys = self.redis.client.keys(pattern)
                if keys:
                    self.redis.client.delete(*keys)
            
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup job {job_id}: {e}")
            return False


class UseCaseOrchestrator:
    """Orchestrates parallel execution of use cases."""
    
    def __init__(self, max_parallel: int = 5):
        self.executor = ParallelDockerExecutor(max_parallel)
        self.running = False
    
    async def execute_job_parallel(self, job_id: str, use_cases: List[Dict[str, Any]], 
                                 repo_path: str, output_dir: str, 
                                 include_folders: List[str]) -> Dict[str, Any]:
        """Execute all use cases for a job in parallel.
        
        Args:
            job_id: Analysis job ID
            use_cases: List of use cases to execute
            repo_path: Repository path
            output_dir: Output directory
            include_folders: Folders to include
            
        Returns:
            Execution summary
        """
        logger.info(f"Starting parallel execution for job {job_id} with {len(use_cases)} use cases")
        
        # Add use cases to queue
        queued_count = self.executor.add_use_cases_to_queue(job_id, use_cases)
        
        if queued_count == 0:
            return {"error": "No use cases to execute"}
        
        # Start orchestration
        self.running = True
        completed_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.executor.max_containers) as executor:
            futures = {}
            
            while self.running:
                # Check for available slots and start new containers
                available_slots = self.executor.get_available_containers()
                
                for _ in range(available_slots):
                    use_case = self.executor.get_next_use_case(job_id)
                    if not use_case:
                        break
                    
                    container_id = f"{job_id}_{use_case['index']}_{str(uuid4())[:8]}"
                    
                    # Start container in thread pool
                    future = executor.submit(
                        self._run_single_use_case,
                        container_id, job_id, use_case, repo_path, output_dir, include_folders
                    )
                    futures[future] = {
                        "container_id": container_id,
                        "use_case_id": use_case["id"]
                    }
                
                # Check completed futures
                completed_futures = [f for f in futures.keys() if f.done()]
                for future in completed_futures:
                    try:
                        result = future.result()
                        if result["exit_code"] == 0:
                            completed_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Container execution failed: {e}")
                        failed_count += 1
                    
                    del futures[future]
                
                # Check if all use cases are processed
                if not futures and not self.executor.get_next_use_case(job_id):
                    break
                
                await asyncio.sleep(2)
        
        # Get final results
        results = self.executor.get_job_results(job_id)
        container_status = self.executor.get_container_status(job_id)
        logs = self.executor.get_job_logs(job_id)
        
        return {
            "job_id": job_id,
            "total_use_cases": len(use_cases),
            "completed": completed_count,
            "failed": failed_count,
            "results": results,
            "container_status": container_status,
            "logs": logs
        }
    
    def _run_single_use_case(self, container_id: str, job_id: str, use_case: Dict[str, Any],
                           repo_path: str, output_dir: str, include_folders: List[str]) -> Dict[str, Any]:
        """Run a single use case in a container."""
        try:
            # Update use case status
            self.executor.update_use_case_status(
                use_case["id"], job_id, "running", 
                {"container_id": container_id}
            )
            
            # Start container
            container = self.executor.start_container(
                container_id, job_id, use_case, repo_path, output_dir, include_folders
            )
            
            # Wait for completion
            result = self.executor.wait_for_container_completion(container, container_id, job_id)
            
            # Update final status
            self.executor.update_use_case_status(
                use_case["id"], job_id, "completed" if result["exit_code"] == 0 else "failed",
                result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error running use case {use_case['id']}: {e}")
            self.executor.update_use_case_status(
                use_case["id"], job_id, "failed", {"error": str(e)}
            )
            return {"container_id": container_id, "exit_code": -1, "error": str(e)}