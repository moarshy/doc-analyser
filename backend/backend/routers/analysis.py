import os
from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
import logging
from backend.models.analysis import AnalysisStatus, AnalysisResult, AnalysisDetail, RepositoryRequest, AnalysisResponse
from backend.services.analysis_service import AnalysisService
from backend.services.auth_service import get_current_user
from backend.services.project_service import project_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["analysis"])
service = AnalysisService()


@router.get("/project/{project_id}/jobs", response_model=List[AnalysisResult])
async def get_project_analyses(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all analysis jobs for a specific project."""
    try:
        # Verify project exists and belongs to user
        project = project_service.get_project(project_id, current_user['id'])
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Get project jobs
        job_ids = project_service.get_project_jobs(project_id, current_user['id'])
        jobs = []
        for job_id_str in job_ids:
            try:
                job_id = UUID(job_id_str)
                job = await service.get_job_status(job_id)
                
                # Convert AnalysisJob to AnalysisResult
                analysis_result = AnalysisResult(
                    job_id=job.id,
                    status=job.status,
                    repository=job.repository_url,
                    use_cases=job.use_cases or [],
                    results=job.results,
                    error=job.error,
                    created_at=job.created_at.isoformat() if job.created_at else None,
                    updated_at=job.updated_at.isoformat() if job.updated_at else None
                )
                jobs.append(analysis_result)
            except ValueError:
                logger.warning(f"Invalid job ID for project {project_id}: {job_id_str}")
                continue
        
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}/detail", response_model=AnalysisDetail)
async def get_analysis_detail(job_id: UUID):
    """Get detailed analysis results including file information."""
    try:
        job = await service.get_job_status(job_id)
        
        # Get job data to extract project_id and file paths
        job_data = service.redis.get_job(job_id)
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": str(job.id),
            "status": job.status,
            "repository": job.repository_url,
            "branch": job_data.get("job_params", {}).get("branch", "main"),
            "include_folders": job_data.get("job_params", {}).get("include_folders", ["docs"]),
            "use_cases": job.use_cases or [],
            "results": job.results,
            "error": job.error,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "project_id": job_data.get("job_params", {}).get("project_id"),
            "data_path": f"/data/{job_id}/data",
            "repo_path": f"/data/{job_id}/repo"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/jobs/{job_id}/files/{filename}")
async def get_analysis_file(
    job_id: UUID,
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific file from analysis results."""
    try:
        job = await service.get_job_status(job_id)
        
        # Check if job belongs to user
        job_data = service.redis.get_job(job_id)
        if not job_data or job_data.get("job_params", {}).get("user_id") != current_user['id']:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Construct file path
        import os
        data_dir = os.getenv("DATA_DIR", "/data")
        file_path = os.path.join(data_dir, str(job_id), "data", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check - ensure file is within job directory
        if not file_path.startswith(os.path.join(data_dir, str(job_id))):
            raise HTTPException(status_code=403, detail="Invalid file path")
            
        return FileResponse(file_path, media_type='text/plain')
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_repository(
    request: RepositoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a repository for analysis."""
    try:
        job_id = await service.submit_analysis(
            url=str(request.url),
            branch=request.branch,
            include_folders=request.include_folders,
            user_id=current_user['id'],
            project_id=request.project_id
        )
        logger.info(f"Analysis task queued: {job_id} for user {current_user['id']}")
        return AnalysisResponse(
            job_id=job_id,
            status=AnalysisStatus.PENDING,
            message="Analysis job submitted successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{job_id}", response_model=AnalysisResult)
async def get_analysis_status(job_id: UUID):
    """Get the status and results of an analysis job."""
    try:
        job = await service.get_job_status(job_id)
        return AnalysisResult(
            job_id=job.id,
            status=job.status,
            repository=job.repository_url,
            use_cases=job.use_cases or [],
            results=job.results,
            error=job.error,
            created_at=job.created_at.isoformat() if job.created_at else None,
            updated_at=job.updated_at.isoformat() if job.updated_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs", response_model=List[AnalysisResult])
async def list_jobs(
    current_user: dict = Depends(get_current_user)
):
    """List user's analysis jobs."""
    jobs = await service.list_user_jobs(
        user_id=current_user['id']
    )
    return [
        AnalysisResult(
            job_id=job.id,
            status=job.status,
            repository=job.repository_url,
            use_cases=job.use_cases or [],
            results=job.results,
            error=job.error,
            created_at=job.created_at.isoformat() if job.created_at else None,
            updated_at=job.updated_at.isoformat() if job.updated_at else None
        )
        for job in jobs
    ]