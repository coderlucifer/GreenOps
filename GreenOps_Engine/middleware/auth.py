"""
GreenOps — Auth Middleware

FastAPI dependency that extracts the current user from:
1. Bearer JWT token (for frontend)
2. X-API-Key header (for SDK / proxy)

Usage in routes:
    from middleware.auth import get_current_user
    
    @router.get("/protected")
    def protected(user = Depends(get_current_user)):
        return {"user_id": user["id"]}
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from services.auth import decode_token
from database import get_user_by_id, get_user_by_api_key

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
) -> Dict[str, Any]:
    """
    Extract the authenticated user from the request.
    
    Checks in order:
    1. Bearer token in Authorization header
    2. X-API-Key header
    
    Raises 401 if neither is valid.
    """
    # Try JWT Bearer token first
    if credentials and credentials.credentials:
        token = credentials.credentials
        payload = decode_token(token)
        if payload and payload.get("type") == "access":
            user_id = int(payload["sub"])
            user = get_user_by_id(user_id)
            if user:
                return user

    # Try API Key
    if api_key:
        user = get_user_by_api_key(api_key)
        if user:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication. Provide a Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    api_key: Optional[str] = Depends(api_key_header),
) -> Optional[Dict[str, Any]]:
    """
    Same as get_current_user but returns None instead of raising 401.
    Useful for public endpoints that optionally personalize for logged-in users.
    """
    try:
        return await get_current_user(credentials, api_key)
    except HTTPException:
        return None

async def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency that enforces the user to have the 'admin' role.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return user
