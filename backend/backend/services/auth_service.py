import os
import jwt
import redis
import logging
import requests
from datetime import datetime, timezone
from typing import Optional, Dict
from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt.algorithms import RSAAlgorithm
from backend.gateway.config import settings

# logging.basicConfig(level=logging.INFO)  # Let the main app configure logging
logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthService:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        self.auth0_domain = settings.AUTH0_DOMAIN
        self.auth0_audience = settings.AUTH0_AUDIENCE
        self._jwks_cache = None
        self._jwks_cache_time = None
        self._jwks_expiry = 3600  # Cache JWKS for 1 hour

    def _get_jwks(self):
        """Get Auth0 JWKS (JSON Web Key Set)"""
        import time
        
        # Cache JWKS for performance
        if self._jwks_cache and self._jwks_cache_time:
            if time.time() - self._jwks_cache_time < self._jwks_expiry:
                return self._jwks_cache
        
        try:
            jwks_url = f"https://{self.auth0_domain}/.well-known/jwks.json"
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            
            self._jwks_cache = jwks
            self._jwks_cache_time = time.time()
            
            return jwks
        except Exception as e:
            logger.error(f"Failed to fetch JWKS: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to fetch authentication keys"
            )

    def _get_public_key(self, kid: str):
        """Get the public key for a given key ID"""
        jwks = self._get_jwks()
        
        for key in jwks.get('keys', []):
            if key['kid'] == kid:
                # Convert JWK to public key
                public_key = RSAAlgorithm.from_jwk(key)
                return public_key
        
        raise HTTPException(status_code=401, detail="Invalid token: unknown key ID")
        
    def verify_token(self, credentials: HTTPAuthorizationCredentials) -> Dict:
        """Verify Auth0 JWT token with proper signature verification"""
        if not credentials:
            raise HTTPException(status_code=401, detail="No authorization header")
            
        try:
            token = credentials.credentials
            
            # Get token header to extract key ID
            headers = jwt.get_unverified_header(token)
            kid = headers.get('kid')
            
            if not kid:
                raise HTTPException(status_code=401, detail="Invalid token: missing key ID")
            
            # Get the public key for this token
            public_key = self._get_public_key(kid)
            
            # Verify the token with the public key
            payload = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=self.auth0_audience,
                issuer=f"https://{self.auth0_domain}/"
            )
            # Ensure we have the required fields
            if not payload.get('sub'):
                raise HTTPException(status_code=401, detail="Invalid token: missing sub")
                
            # Extract user data from verified token
            # Handle both ID tokens and access tokens with different audience formats
            email = payload.get('email')
            
            # Fallback for access tokens that don't include email
            if not email or email == f"{payload['sub']}@placeholder.com":
                # For access tokens without email, we'll use the sync-user endpoint data
                # The sync-user endpoint should provide the actual email from Auth0 user object
                email = None  # Will be provided by the sync-user payload
            
            name = payload.get('name') or payload.get('nickname') or (email.split('@')[0] if email else payload['sub'])
            picture = payload.get('picture') or ''
                        
            return {
                'sub': payload['sub'],
                'email': email,
                'name': name,
                'picture': picture
            }
            
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")
    
    def get_or_create_user(self, user_info: Dict) -> Dict:
        """Get or create user in Redis"""
        user_id = user_info['sub']
        email = user_info['email']  # This comes from frontend Auth0 user object
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        user_key = f"user:{user_id}"
        
        # Check if user exists
        existing_user = self.redis_client.hgetall(user_key)
        
        if existing_user:
            # Update last login
            self.redis_client.hset(user_key, "last_login", datetime.now(timezone.utc).isoformat())
            return {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": existing_user.get("created_at"),
                "last_login": datetime.now(timezone.utc).isoformat(),
                "total_jobs": int(existing_user.get("total_jobs", 0))
            }
        else:
            # Create new user
            now = datetime.now(timezone.utc).isoformat()
            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": now,
                "last_login": now,
                "total_jobs": 0
            }
            
            # Store user data
            self.redis_client.hset(user_key, mapping=user_data)
            
            return user_data
    
    def increment_user_job_count(self, user_id: str):
        """Increment user's job count"""
        user_key = f"user:{user_id}"
        self.redis_client.hincrby(user_key, "total_jobs", 1)
    
    def get_user_jobs(self, user_id: str) -> list:
        """Get all job IDs for a user"""
        jobs_key = f"user_jobs:{user_id}"
        return self.redis_client.lrange(jobs_key, 0, -1)
    
    def link_job_to_user(self, user_id: str, job_id: str):
        """Link a job to a user"""
        jobs_key = f"user_jobs:{user_id}"
        self.redis_client.lpush(jobs_key, job_id)

# Global auth service instance
auth_service = AuthService()

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Dependency to get current authenticated user ID (sub) from token"""
    user_info = auth_service.verify_token(credentials)
    return user_info['sub']

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
    """Dependency to get current authenticated user from Redis"""
    user_info = auth_service.verify_token(credentials)
    user_id = user_info['sub']
    
    # Get user from Redis (must exist after sync-user call)
    user_key = f"user:{user_id}"
    user_data = auth_service.redis_client.hgetall(user_key)
    
    if not user_data:
        raise HTTPException(
            status_code=404, 
            detail="User not found. Please sync user first by calling /auth/sync-user"
        )
    
    return {
        "id": user_id,
        "email": user_data["email"],
        "name": user_data["name"], 
        "picture": user_data["picture"],
        "created_at": user_data["created_at"],
        "last_login": user_data["last_login"],
        "total_jobs": int(user_data["total_jobs"])
    }