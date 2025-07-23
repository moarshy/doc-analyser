from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List
from backend.services.auth_service import get_current_user
from backend.models.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from backend.services.project_service import project_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        project = project_service.create_project(current_user['id'], project_data)
        logger.info(f"Created project: {project}")
        return ProjectResponse(**project.model_dump())
    except Exception as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user)
):
    """List user's projects with pagination"""
    try:
        projects, total = project_service.list_user_projects(
            current_user['id'], page, per_page
        )
        
        project_responses = [
            ProjectResponse(**project.model_dump()) 
            for project in projects
        ]
        
        return ProjectListResponse(
            projects=project_responses,
            total=total,
            page=page,
            per_page=per_page
        )
    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list projects")

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get a specific project"""
    try:
        project = project_service.get_project(project_id, current_user['id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return ProjectResponse(**project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project")

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update a project"""
    try:
        project = project_service.update_project(project_id, current_user['id'], update_data)
        return ProjectResponse(**project.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update project")

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a project"""
    try:
        success = project_service.delete_project(project_id, current_user['id'])
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete project")

@router.get("/{project_id}/jobs")
async def get_project_jobs(
    project_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get all jobs for a project"""
    try:
        job_ids = project_service.get_project_jobs(project_id, current_user['id'])
        
        # For now, just return job IDs
        # TODO: Integrate with analysis service to get full job details
        return {"project_id": project_id, "job_ids": job_ids}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get jobs for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get project jobs")