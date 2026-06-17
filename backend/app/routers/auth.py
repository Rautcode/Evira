import os
from fastapi import APIRouter, HTTPException, status, Request, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.user_service import verify_user
from app.core.security import decode_token, get_current_user
import jwt
from datetime import datetime, timedelta, timezone

router = APIRouter(tags=["auth"], prefix="/auth")
security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: JWT_SECRET environment variable is not set. Refusing to start with an insecure default.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest = Body(...)):
    """Simple username/password login against app user accounts."""
    user = verify_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user["username"],
        "exp": expire,
        "user": user["username"],
        "role": user.get("role", "operator"),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"success": True, "user": user["username"], "role": user.get("role", "operator"), "token": token}

@router.get("/verify")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    return {"success": True, "user": payload.get("user")}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user (frontend calls this on load)."""
    return {
        "success": True,
        "user": current_user.get("user"),
        "username": current_user.get("sub"),
        "role": current_user.get("role", "operator"),
    }

@router.post("/logout")
def logout():
    """Stateless JWT logout. The client discards its token; nothing to do server-side."""
    return {"success": True, "message": "Logged out"}

@router.get("/login")
def login_get():
    """Handle incorrect GET requests to login endpoint"""
    raise HTTPException(
        status_code=405,
        detail="Method not allowed. Use POST to /auth/login with login credentials."
    )
