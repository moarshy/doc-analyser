import uuid
import json
import logging
import redis
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException
from backend.models.project import Project, ProjectCreate, ProjectUpdate, ProjectStatus

logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self):
        # Use direct Redis client for project operations
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )

    def create_project(self, user_id: str, project_data: ProjectCreate) -> Project:
        """Create a new project for a user"""
        project_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        project = Project(
            id=project_id,
            name=project_data.name,
            description=project_data.description,
            repository_url=project_data.repository_url,
            user_id=user_id,
            status=ProjectStatus.active,
            settings=project_data.settings or {},
            created_at=now,
            updated_at=now,
            job_count=0,
            last_analysis_at=None
        )
        
        # Store project in Redis
        project_key = f"project:{project_id}"
        project_data_for_redis = project.model_dump()
        
        # Handle None values and serialize complex types
        for key, value in project_data_for_redis.items():
            if value is None:
                project_data_for_redis[key] = ""  # Convert None to empty string
            elif key == 'settings':
                project_data_for_redis[key] = json.dumps(value)
            elif key == 'status':
                # Handle enum - extract the actual string value
                if hasattr(value, 'value'):
                    project_data_for_redis[key] = value.value
                elif isinstance(value, str) and value.startswith('ProjectStatus.'):
                    # Handle case where it's already converted to string representation
                    project_data_for_redis[key] = value.split('.')[-1]
                else:
                    project_data_for_redis[key] = str(value)
            else:
                project_data_for_redis[key] = str(value)
        
        self.redis.hset(project_key, mapping=project_data_for_redis)
        
        # Add to user's project list
        user_projects_key = f"user_projects:{user_id}"
        timestamp = datetime.now(timezone.utc).timestamp()
        self.redis.zadd(user_projects_key, {project_id: timestamp})
        
        # Set TTL (30 days)
        self.redis.expire(project_key, 30 * 24 * 60 * 60)
        self.redis.expire(user_projects_key, 30 * 24 * 60 * 60)
        
        logger.info(f"Created project {project_id} for user {user_id}")
        return project

    def get_project(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a project by ID if user owns it"""
        project_key = f"project:{project_id}"
        project_data = self.redis.hgetall(project_key)
        
        if not project_data:
            return None
            
        # Verify ownership
        if project_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this project")
        
        # Convert Redis data back to Project model
        # Handle empty strings as None for optional fields
        for key, value in project_data.items():
            if value == "":
                if key in ['description', 'repository_url', 'last_analysis_at']:
                    project_data[key] = None
            elif key == 'status' and isinstance(value, str) and value.startswith('ProjectStatus.'):
                # Fix any existing bad enum data
                project_data[key] = value.split('.')[-1]
        
        # Deserialize JSON fields
        if project_data.get('settings'):
            project_data['settings'] = json.loads(project_data['settings'])
        else:
            project_data['settings'] = {}
            
        # Convert numeric fields
        project_data['job_count'] = int(project_data.get('job_count', 0))
        
        return Project(**project_data)

    def update_project(self, project_id: str, user_id: str, update_data: ProjectUpdate) -> Project:
        """Update a project"""
        project = self.get_project(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Handle None values and serialize complex types
        for key, value in list(update_dict.items()):
            if value is None:
                update_dict[key] = ""  # Convert None to empty string
            elif key == 'settings':
                update_dict[key] = json.dumps(value)
            elif key == 'status':
                # Handle enum - extract the actual string value
                if hasattr(value, 'value'):
                    update_dict[key] = value.value
                elif isinstance(value, str) and value.startswith('ProjectStatus.'):
                    # Handle case where it's already converted to string representation
                    update_dict[key] = value.split('.')[-1]
                else:
                    update_dict[key] = str(value)
            else:
                update_dict[key] = str(value)
        
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update in Redis
        project_key = f"project:{project_id}"
        self.redis.hset(project_key, mapping=update_dict)
        
        # Get updated project
        return self.get_project(project_id, user_id)

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Soft delete a project"""
        project = self.get_project(project_id, user_id)
        if not project:
            return False
        
        # Soft delete by updating status
        project_key = f"project:{project_id}"
        self.redis.hset(project_key, mapping={
            'status': ProjectStatus.deleted.value,
            'updated_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Remove from user's active projects list
        user_projects_key = f"user_projects:{user_id}"
        self.redis.zrem(user_projects_key, project_id)
        
        logger.info(f"Deleted project {project_id} for user {user_id}")
        return True

    def list_user_projects(self, user_id: str, page: int = 1, per_page: int = 20) -> tuple[List[Project], int]:
        """List projects for a user with pagination"""
        user_projects_key = f"user_projects:{user_id}"
        
        # Get total count
        total = self.redis.zcard(user_projects_key)
        
        # Get paginated project IDs (sorted by creation time, newest first)
        start = (page - 1) * per_page
        end = start + per_page - 1
        project_ids = self.redis.zrevrange(user_projects_key, start, end)
        
        # Get project details
        projects = []
        for project_id in project_ids:
            project = self.get_project(project_id, user_id)
            if project and project.status != ProjectStatus.deleted:
                projects.append(project)
        
        return projects, total

    def increment_job_count(self, project_id: str):
        """Increment job count for a project"""
        project_key = f"project:{project_id}"
        self.redis.hincrby(project_key, 'job_count', 1)
        self.redis.hset(project_key, 'last_analysis_at', datetime.now(timezone.utc).isoformat())

    def get_project_jobs(self, project_id: str, user_id: str) -> List[str]:
        """Get all job IDs for a project"""
        # Verify project ownership first
        project = self.get_project(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_jobs_key = f"project_jobs:{project_id}"
        return self.redis.lrange(project_jobs_key, 0, -1)

    def link_job_to_project(self, project_id: str, job_id: str):
        """Link a job to a project"""
        project_jobs_key = f"project_jobs:{project_id}"
        self.redis.lpush(project_jobs_key, job_id)
        
        # Update project job count and last analysis time
        self.increment_job_count(project_id)

# Global service instance
project_service = ProjectService()