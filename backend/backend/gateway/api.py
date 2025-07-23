from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, HttpUrl
import logging
from backend.models.analysis import AnalysisStatus, AnalysisJob
from backend.services.analyse_service import AnalysisService
from backend.services.auth_service import get_current_user

logger = logging.getLogger("backend.gateway.api")
logger = logging.getLogger(__name__)

router = APIRouter()
service = AnalysisService()


class RepositoryRequest(BaseModel):
    url: HttpUrl
    branch: str = "main"
    include_folders: List[str] = ["docs"]
    project_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    job_id: UUID
    status: AnalysisStatus
    message: str


class AnalysisResult(BaseModel):
    job_id: UUID
    status: AnalysisStatus
    repository: str
    use_cases: List[dict]
    results: Optional[dict] = None
    error: Optional[str] = None


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
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs", response_model=List[AnalysisResult])
async def list_jobs(
    skip: int = 0, 
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """List user's analysis jobs."""
    jobs = await service.list_user_jobs(
        user_id=current_user['id'],
        skip=skip, 
        limit=limit
    )
    return [
        AnalysisResult(
            job_id=job.id,
            status=job.status,
            repository=job.repository_url,
            use_cases=job.use_cases or [],
            results=job.results,
            error=job.error,
        )
        for job in jobs
    ]


# Import and include routers
from backend.routers.auth import router as auth_router
from backend.routers.projects import router as projects_router

router.include_router(auth_router, prefix="/auth")
router.include_router(projects_router)