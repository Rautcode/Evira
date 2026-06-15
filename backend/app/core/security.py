"""Shared authentication dependencies.

Centralizes JWT verification so every protected router can enforce auth via
`Depends(get_current_user)` without duplicating decode logic or importing the
auth router (which would create a circular import).
"""

import os
import logging
from typing import Dict, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise RuntimeError(
        "CRITICAL: JWT_SECRET environment variable is not set. "
        "Refusing to start with an insecure default."
    )
ALGORITHM = "HS256"

# auto_error=False lets us raise our own 401 with a WWW-Authenticate header
# instead of FastAPI's default 403 when the Authorization header is missing.
_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT, raising 401 on any problem."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise _CREDENTIALS_EXC


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> Dict[str, Any]:
    """FastAPI dependency: require a valid Bearer token, return its claims."""
    if credentials is None or not credentials.credentials:
        raise _CREDENTIALS_EXC
    return decode_token(credentials.credentials)


def verify_ws_token(token: str | None) -> Dict[str, Any] | None:
    """Validate a WebSocket token (passed as a query param, since browsers
    cannot set an Authorization header on WS). Returns claims or None."""
    if not token:
        return None
    try:
        return decode_token(token)
    except HTTPException:
        return None
