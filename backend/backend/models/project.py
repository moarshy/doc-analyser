from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProjectStatus(str, Enum):
    active = "active"
    archived = "archived"
    deleted = "deleted"

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    repository_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    status: Optional[ProjectStatus] = None

class Project(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    user_id: str
    status: ProjectStatus = ProjectStatus.active
    settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    job_count: int = 0
    last_analysis_at: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    status: ProjectStatus
    settings: Dict[str, Any]
    created_at: str
    updated_at: str
    job_count: int
    last_analysis_at: Optional[str] = None

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    per_page: int