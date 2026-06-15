import os
from fastapi import APIRouter, HTTPException, status, Request, Body, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.auth_service import validate_sql_login
from app.core.security import decode_token, get_current_user
from fastapi.responses import JSONResponse
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
    auth_type: str  # 'sql' or 'windows'
    server: str | None = None
    database: str | None = None
    username: str
    password: str | None = None

@router.post("/login")
def login(data: LoginRequest = Body(...)):
    server = data.server or os.getenv("MSSQL_SERVER", "localhost")
    database = data.database or os.getenv("MSSQL_DATABASE", "scada_reports")
    
    if data.auth_type == "sql" and not all([data.username, data.password]):
        raise HTTPException(
            status_code=400,
            detail="Username and password are required for SQL authentication"
        )
    elif data.auth_type == "windows" and not data.username:
        raise HTTPException(
            status_code=400,
            detail="Username is required for Windows authentication"
        )
        
    result = validate_sql_login(
        server=server,
        database=database,
        username=data.username,
        password=data.password or "",
        auth_type=data.auth_type
    )
    if result.get("success"):
        # Generate JWT token
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": data.username,
            "exp": expire,
            "user": result["user"]
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return {"success": True, "user": result["user"], "token": token}
    else:
        raise HTTPException(status_code=401, detail=result.get("error", "Login failed"))

@router.get("/verify")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    return {"success": True, "user": payload.get("user")}

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user (frontend calls this on load)."""
    return {"success": True, "user": current_user.get("user"), "username": current_user.get("sub")}

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
