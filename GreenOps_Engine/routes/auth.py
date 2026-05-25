"""
GreenOps — Auth Routes

User registration, login, token refresh, profile, and API key management.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
)
from database import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_api_keys,
    get_demo_user_id,
    get_db,
    DEMO_EMAIL,
    DEMO_PASSWORD,
)
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================================
# ROUTES
# ============================================================

@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    """Create a new user account."""
    # Check if email already exists
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Validate password strength
    if len(req.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Create user
    hashed = hash_password(req.password)
    user_data = create_user(req.name, req.email, hashed)

    # Generate tokens
    access = create_access_token(user_data["id"], req.email)
    refresh = create_refresh_token(user_data["id"])

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user_data["id"],
            "name": req.name,
            "email": req.email,
            "api_key": user_data["api_key"],
            "is_demo": False,
        },
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Login with email and password."""
    user = get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access = create_access_token(user["id"], user["email"])
    refresh = create_refresh_token(user["id"])

    # Get first API key
    keys = get_user_api_keys(user["id"])
    api_key = keys[0]["key"] if keys else None

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "api_key": api_key,
            "is_demo": bool(user.get("is_demo", 0)),
        },
    )


@router.post("/demo", response_model=TokenResponse)
def demo_login():
    """Login as the demo user — no credentials needed."""
    user = get_user_by_email(DEMO_EMAIL)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo user not configured",
        )

    access = create_access_token(user["id"], user["email"])
    refresh = create_refresh_token(user["id"])

    keys = get_user_api_keys(user["id"])
    api_key = keys[0]["key"] if keys else None

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "api_key": api_key,
            "is_demo": True,
        },
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshRequest):
    """Refresh an expired access token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = int(payload["sub"])
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access = create_access_token(user["id"], user["email"])
    refresh = create_refresh_token(user["id"])

    keys = get_user_api_keys(user["id"])
    api_key = keys[0]["key"] if keys else None

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        user={
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "api_key": api_key,
            "is_demo": bool(user.get("is_demo", 0)),
        },
    )


@router.get("/me")
def get_me(user=Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    keys = get_user_api_keys(user["id"])
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "is_demo": bool(user.get("is_demo", 0)),
        "created_at": user.get("created_at"),
        "api_keys": keys,
    }


@router.post("/api-keys")
def create_api_key(label: str = "default", user=Depends(get_current_user)):
    """Generate a new API key for the authenticated user."""
    if user.get("is_demo"):
        raise HTTPException(status_code=403, detail="Demo users cannot create API keys")

    new_key = generate_api_key()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO api_keys (user_id, key, label) VALUES (?, ?, ?)",
            (user["id"], new_key, label),
        )

    return {"key": new_key, "label": label, "message": "API key created"}


@router.delete("/api-keys/{key_id}")
def revoke_api_key(key_id: int, user=Depends(get_current_user)):
    """Revoke an API key."""
    if user.get("is_demo"):
        raise HTTPException(status_code=403, detail="Demo users cannot revoke API keys")

    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM api_keys WHERE id = ? AND user_id = ?",
            (key_id, user["id"]),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key revoked"}
