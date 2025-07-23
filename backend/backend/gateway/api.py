from fastapi import APIRouter
import logging
# Import and include routers
from backend.routers.auth import router as auth_router
from backend.routers.projects import router as projects_router
from backend.routers.analysis import router as analysis_router


logger = logging.getLogger("backend.gateway.api")
logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
router.include_router(projects_router, prefix="/projects")
router.include_router(analysis_router, prefix="/analysis")


# health check
@router.get("/health")
async def health_check():
    return {"status": "ok"}