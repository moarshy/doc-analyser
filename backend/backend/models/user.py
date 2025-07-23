from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: str  # Auth0 user_id (sub)
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: datetime
    last_login: datetime
    total_jobs: int = 0

class UserCreate(BaseModel):
    auth0_id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: datetime
    last_login: datetime
    total_jobs: int = 0

class AuthRequest(BaseModel):
    token: str  # JWT token from frontend