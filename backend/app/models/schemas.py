"""Model schemas for the Evira application."""

from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

class WinCCStatus(BaseModel):
    """WinCC connection status and statistics."""
    connected: bool
    total_tags: int
    active_tags: int

class SystemStatus(BaseModel):
    """Overall system status."""
    database: bool
    wincc: WinCCStatus
    email: bool
    report_engine: bool

class ReportStats(BaseModel):
    """Report generation statistics."""
    total: int
    successful: int
    failed: int
    by_type: Dict[str, int]

class SchedulerStats(BaseModel):
    """Task scheduler statistics."""
    total: int
    active: int
    upcoming_24h: int

class ActivityEvent(BaseModel):
    """System activity event."""
    event_type: str
    description: str
    severity: str
    created_at: str
    user: Optional[str]
    source: Optional[str]
    metadata: Optional[str]

class DashboardData(BaseModel):
    """Complete dashboard data."""
    system_status: SystemStatus
    reports: ReportStats
    scheduler: SchedulerStats
    recent_activity: List[ActivityEvent]
    last_updated: str
