from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CLONING = "cloning"
    EXTRACTING = "extracting"
    EXTRACTING_USE_CASES = "extracting_use_cases"
    EXECUTING = "executing"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"
    EXTRACTION_FAILED = "extraction_failed"
    TIMEOUT = "timeout"


class AnalysisJob(BaseModel):
    id: UUID
    repository_url: str
    branch: str
    include_folders: List[str]
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None  # Auth0 user_id
    use_cases: Optional[List[Dict]] = None
    results: Optional[Dict] = None
    error: Optional[str] = None


class JobCreate(BaseModel):
    repository_url: HttpUrl
    branch: str = "main"
    include_folders: List[str] = ["docs"]


class AnalysisResult(BaseModel):
    job_id: UUID
    status: AnalysisStatus
    repository: str
    use_cases: List[dict]
    results: Optional[dict] = None
    error: Optional[str] = None


class AnalysisDetail(BaseModel):
    job_id: UUID
    status: AnalysisStatus
    repository: str
    branch: str
    include_folders: List[str]
    use_cases: List[dict]
    results: Optional[dict] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    project_id: Optional[str] = None

class RepositoryRequest(BaseModel):
    url: HttpUrl
    branch: str = "main"
    include_folders: List[str] = ["docs"]
    project_id: Optional[str] = None


class AnalysisResponse(BaseModel):
    job_id: UUID
    status: AnalysisStatus
    message: str