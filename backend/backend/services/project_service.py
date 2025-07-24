import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException
from backend.models.project import Project, ProjectCreate, ProjectUpdate, ProjectStatus
from backend.common.redis_client import get_redis_client

logger = logging.getLogger(__name__)

class ProjectService:
    def __init__(self):
        # Use unified Redis client for project operations
        self.redis = get_redis_client()

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
        
        # Store project in Redis using JSON format
        project_data_for_redis = project.model_dump()
        
        # Handle enum serialization
        if hasattr(project_data_for_redis['status'], 'value'):
            project_data_for_redis['status'] = project_data_for_redis['status'].value
        
        self.redis.store_project(project_id, project_data_for_redis)
        
        # Add to user's project list
        self.redis.add_user_project(user_id, project_id)
        
        logger.info(f"Created project {project_id} for user {user_id}")
        return project

    def get_project(self, project_id: str, user_id: str) -> Optional[Project]:
        """Get a project by ID if user owns it"""
        project_data = self.redis.get_project(project_id)
        
        if not project_data:
            return None
            
        # Verify ownership
        if project_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this project")
        
        # Convert numeric fields
        project_data['job_count'] = int(project_data.get('job_count', 0))
        
        # Ensure settings is a dict
        if not isinstance(project_data.get('settings'), dict):
            project_data['settings'] = {}
        
        return Project(**project_data)

    def update_project(self, project_id: str, user_id: str, update_data: ProjectUpdate) -> Project:
        """Update a project"""
        project = self.get_project(project_id, user_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Handle enum serialization
        if 'status' in update_dict and hasattr(update_dict['status'], 'value'):
            update_dict['status'] = update_dict['status'].value
        
        update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Get current project data and update it
        current_data = self.redis.get_project(project_id)
        if current_data:
            current_data.update(update_dict)
            self.redis.store_project(project_id, current_data)
        
        # Get updated project
        return self.get_project(project_id, user_id)

    def delete_project(self, project_id: str, user_id: str) -> bool:
        """Soft delete a project"""
        project = self.get_project(project_id, user_id)
        if not project:
            return False
        
        # Soft delete by updating status
        self.redis.update_project_field(project_id, 'status', ProjectStatus.deleted.value)
        
        logger.info(f"Deleted project {project_id} for user {user_id}")
        return True

    def list_user_projects(self, user_id: str) -> tuple[List[Project], int]:
        """List all projects for a user"""
        # Get all project IDs (sorted by creation time, newest first)
        project_ids = self.redis.get_user_projects_list(user_id)
        
        # Get project details
        projects = []
        for project_id in project_ids:
            project = self.get_project(project_id, user_id)
            if project and project.status != ProjectStatus.deleted:
                projects.append(project)
        
        return projects, len(projects)

    def increment_job_count(self, project_id: str):
        """Increment job count for a project"""
        project_data = self.redis.get_project(project_id)
        if project_data:
            project_data['job_count'] = int(project_data.get('job_count', 0)) + 1
            project_data['last_analysis_at'] = datetime.now(timezone.utc).isoformat()
            self.redis.store_project(project_id, project_data)

    def get_project_jobs(self, project_id: str, user_id: str) -> List[str]:
        """Get all job IDs for a project"""
        try:
            # Verify project ownership first
            project = self.get_project(project_id, user_id)
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            return self.redis.get_project_jobs_list(project_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to get project jobs")

    def link_job_to_project(self, project_id: str, job_id: str):
        """Link a job to a project"""
        self.redis.add_project_job(project_id, job_id)
        
        # Update project job count and last analysis time
        self.increment_job_count(project_id)

# Global service instance
project_service = ProjectService()