"""
CivicMind AI — Admin Authentication Routes
Demo-friendly role-based authentication for municipal administrators.
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.core.config import Settings
import hashlib
import time

router = APIRouter(tags=["Authentication"])
settings = Settings()

class LoginRequest(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    username: str
    role: str
    name: str
    department: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

def create_demo_token(username: str, role: str) -> str:
    raw = f"{username}:{role}:{settings.JWT_SECRET_KEY}:{int(time.time() // 86400)}"
    sig = hashlib.sha256(raw.encode()).hexdigest()[:24]
    return f"cm_token_{username}_{sig}"

def verify_demo_token(token: Optional[str]) -> Dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    clean_token = token.replace("Bearer ", "").strip()
    if not clean_token.startswith("cm_token_admin_"):
        raise HTTPException(status_code=401, detail="Invalid admin session token")
    return {
        "username": settings.ADMIN_USERNAME,
        "role": "admin",
        "name": "Municipal Chief Administrator",
        "department": "Greater Chennai Corporation — Command Center",
    }

@router.post("/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    Authenticate municipal administrator with demo-friendly credentials.
    """
    if req.username.strip() != settings.ADMIN_USERNAME or req.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=401,
            detail="Invalid administrative username or password. Default is admin / civicmind2026",
        )

    token = create_demo_token(settings.ADMIN_USERNAME, "admin")
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(
            username=settings.ADMIN_USERNAME,
            role="admin",
            name="Municipal Chief Administrator",
            department="Greater Chennai Corporation — Command Center",
        ),
    )

@router.get("/auth/me", response_model=UserProfile)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Returns profile information of currently authenticated admin.
    """
    user_data = verify_demo_token(authorization)
    return UserProfile(**user_data)

@router.post("/auth/logout")
async def logout():
    """
    Terminates admin session.
    """
    return {"success": True, "message": "Logged out successfully"}
