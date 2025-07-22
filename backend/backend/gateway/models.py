from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisJob(BaseModel):
    id: UUID
    repository_url: str
    branch: str
    include_folders: List[str]
    status: AnalysisStatus
    created_at: datetime
    updated_at: datetime
    use_cases: Optional[List[Dict]] = None
    results: Optional[Dict] = None
    error: Optional[str] = None


class JobCreate(BaseModel):
    repository_url: HttpUrl
    branch: str = "main"
    include_folders: List[str] = ["docs"]