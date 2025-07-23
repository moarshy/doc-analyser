from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from backend.common.auth import get_current_user, get_current_user_id, auth_service
from backend.models.user import User, UserCreate, AuthRequest, UserResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

@router.post("/sync-user")
async def sync_user(user_data: UserCreate, current_user_id: str = Depends(get_current_user_id)):
    """
    Sync Auth0 user with backend. This endpoint creates or updates user data.
    """
    logger.info(f"Syncing user: {user_data}")
    # Verify the token's user ID matches the provided user data
    if current_user_id != user_data.auth0_id:
        raise HTTPException(
            status_code=403, 
            detail="Token user ID does not match provided user data"
        )
    
    # Use the provided user data from the frontend (from Auth0 user object)
    user_info = {
        'sub': user_data.auth0_id,
        'email': user_data.email,
        'name': user_data.name,
        'picture': user_data.picture
    }
    
    # Create or update user with the provided data
    user = auth_service.get_or_create_user(user_info)
    
    return UserResponse(
        id=user['id'],
        email=user['email'],
        name=user['name'],
        picture=user['picture'],
        created_at=user['created_at'],
        last_login=user['last_login'],
        total_jobs=user['total_jobs']
    )

@router.get("/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """
    Get current authenticated user profile
    """
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        name=current_user['name'],
        picture=current_user['picture'],
        created_at=current_user['created_at'],
        last_login=current_user['last_login'],
        total_jobs=current_user['total_jobs']
    )

@router.get("/validate")
async def validate_token(current_user: Dict = Depends(get_current_user)):
    """
    Validate the current JWT token
    """
    return {"valid": True, "user": current_user}