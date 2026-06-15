"""Response models for report-related endpoints."""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class MachineInfo(BaseModel):
    """Machine information model."""
    id: str
    name: str
    status: Optional[str] = None
    last_active: Optional[datetime] = None

class ReportGenerateResponse(BaseModel):
    """Response model for report generation."""
    success: bool
    file_path: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class MachineItem(BaseModel):
    """Individual machine information."""
    id: str
    name: str
    type: str
    status: Optional[str] = None
    last_active: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    total_reports: Optional[int] = 0
    is_available: bool = True

class MachineListResponse(BaseModel):
    """Response model for machine list endpoint."""
    message: str
    data: Dict[str, List[MachineItem]]
