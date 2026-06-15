"""Response models for API endpoints."""

from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

class SuccessResponse(BaseModel):
    """Standard success response model."""
    status: str = "success"
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = str(datetime.now())

class ErrorResponse(BaseModel):
    """Standard error response model."""
    status: str = "error"
    error: str
    detail: str
    suggestion: Optional[str] = None
    docs_url: Optional[str] = None
    timestamp: str = str(datetime.now())
