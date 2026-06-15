import logging
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from app.models.responses import SuccessResponse
from app.utils.db import (
    get_connection_status,
    get_recent_reports,
    get_scheduled_tasks,
    get_recent_events,
    get_db_connection,
)
from app.services.wincc_service import wincc_monitor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"], prefix="/dashboard")

@router.get("", response_model=SuccessResponse)  # Empty path route
@router.get("/", response_model=SuccessResponse)  # Root path route
def get_dashboard():
    """Get basic dashboard info"""
    return SuccessResponse(
        message="Welcome to the SCADA Report Dashboard",
        data={
            "timestamp": str(datetime.now()),
            "available_endpoints": {
                "/dashboard": "This endpoint (dashboard overview)",
                "/dashboard/stats": "Dashboard statistics",
                "/ws/dashboard": "WebSocket for real-time updates"
            }
        }
    )

@router.get("/stats")
def get_dashboard_stats():
    """Get all dashboard statistics in real-time"""
    try:
        # Get system status
        system_status = {
            "database": get_connection_status(),
            "wincc": wincc_monitor.get_status(),
            "email": get_connection_status("email"),
            "report_engine": get_connection_status("report")
        }
        
        # Get report statistics for the last 7 days
        report_stats = get_recent_reports(days=7)
        
        # Get scheduler statistics
        scheduler_stats = get_scheduled_tasks()
        
        # Get recent activity
        recent_activity = get_recent_events(limit=5)
        
        return {
            "system_status": system_status,
            "reports": report_stats,
            "scheduler": scheduler_stats,
            "recent_activity": recent_activity,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        logger.exception("Failed to build dashboard stats")
        raise HTTPException(status_code=500, detail="Failed to load dashboard statistics")

@router.get("/activity")
def get_activity_feed(limit: int = Query(10, ge=1, le=100)):
    """Get recent activity feed"""
    try:
        return get_recent_events(limit=limit)
    except Exception as e:
        logger.exception("Failed to fetch activity feed")
        raise HTTPException(status_code=500, detail="Failed to load activity feed")

@router.get("/scada/tags")
def get_scada_tags():
    """Get all discovered and configured SCADA tags from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    SELECT
                        id,
                        tag_name,
                        tag_type,
                        description,
                        value,
                        quality,
                        last_update,
                        machine_id,
                        active
                    FROM wincc_tags
                    ORDER BY machine_id, tag_name
                """)
                tags = []
                for row in cursor.fetchall():
                    desc = row.description
                    # handle possible NTEXT type display mapping if needed
                    if desc is not None:
                        desc = str(desc)
                    # SCADA tag values may be non-numeric (textual/boolean); never let
                    # one bad value abort the whole response.
                    try:
                        value = float(row.value) if row.value is not None else None
                    except (ValueError, TypeError):
                        value = None
                    tags.append({
                        "id": row.id,
                        "tag_name": row.tag_name,
                        "tag_type": row.tag_type,
                        "description": desc,
                        "value": value,
                        "quality": row.quality or "Unknown",
                        "last_update": row.last_update.isoformat() if row.last_update else None,
                        "machine_id": row.machine_id,
                        "active": bool(row.active)
                    })
                return tags
            finally:
                cursor.close()
    except Exception as e:
        logger.exception("Failed to fetch SCADA tags")
        raise HTTPException(status_code=500, detail="Failed to fetch SCADA tags")

