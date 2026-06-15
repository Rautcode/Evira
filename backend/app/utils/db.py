"""Database utility functions."""

import pyodbc
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from app.utils.db_connector import DBConnector
from app.utils.shared_utils import handle_db_error
from app.utils.db_pool import get_db_connection

logger = logging.getLogger(__name__)

@handle_db_error
def get_connection_status(connection_type: str = "database") -> bool:
    """Check if a service connection is working."""
    if connection_type == "database":
        from app.utils.db_pool import pool
        try:
            conn = pool.get_connection()
            pool.return_connection(conn)
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    elif connection_type == "email":
        from app.services.email_service import email_service
        return email_service.check_connection()
    elif connection_type == "report":
        # TODO: Implement report engine status check
        return True
    else:
        logger.warning(f"Unknown connection type: {connection_type}")
        return False

@handle_db_error
def get_recent_reports(days: int = 7) -> Dict[str, Any]:
    """Get statistics about recently generated reports."""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get report statistics
            stats_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as failed,
                    report_type
                FROM report_history
                WHERE created_at >= ? AND created_at <= ?
                GROUP BY report_type
            """
            
            cursor.execute(stats_query, (start_date, end_date))
            results = cursor.fetchall()
            
            # Aggregate totals and group by type
            total = 0
            successful = 0
            failed = 0
            by_type = {}
            
            for row in results:
                total += row[0]
                successful += row[1]
                failed += row[2]
                by_type[row[3]] = row[0]
                
            return {
                "total": total,
                "successful": successful,
                "failed": failed,
                "by_type": by_type
            }
                
    except Exception as e:
        raise RuntimeError(f"Failed to get report statistics: {e}")

@handle_db_error
def get_wincc_status() -> Dict[str, Any]:
    """Get WinCC connection status and statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            status_query = """
                SELECT
                    COUNT(*) as total_tags,
                    SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active_tags
                FROM wincc_tags
            """
            
            cursor.execute(status_query)
            row = cursor.fetchone()
            
            return {
                "connected": True,
                "total_tags": row[0],
                "active_tags": row[1] if row[1] is not None else 0
            }
            
    except Exception:
        return {
            "connected": False,
            "total_tags": 0,
            "active_tags": 0
        }

@handle_db_error
def get_scheduled_tasks() -> Dict[str, Any]:
    """Get task scheduler statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get task statistics
            stats_query = """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN next_run <= DATEADD(HOUR, 24, GETDATE()) THEN 1 ELSE 0 END) as upcoming
                FROM scheduled_tasks
            """
            
            cursor.execute(stats_query)
            row = cursor.fetchone()
            
            return {
                "total": row[0],
                "active": row[1] if row[1] is not None else 0,
                "upcoming_24h": row[2] if row[2] is not None else 0
            }
            
    except Exception as e:
        raise RuntimeError(f"Failed to get scheduler statistics: {e}")

@handle_db_error
def get_recent_events(limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent system events."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            events_query = """
                SELECT
                    event_type,
                    description,
                    severity,
                    created_at,
                    user_id,
                    source,
                    metadata
                FROM activity_log
                ORDER BY created_at DESC
                OFFSET 0 ROWS
                FETCH NEXT ? ROWS ONLY
            """
            
            cursor.execute(events_query, (limit,))
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "event_type": row[0],
                    "description": row[1],
                    "severity": row[2],
                    "created_at": row[3].isoformat() if row[3] else None,
                    "user": row[4],
                    "source": row[5],
                    "metadata": row[6]
                })
                
            return events
            
    except Exception as e:
        raise RuntimeError(f"Failed to get recent events: {e}")

@handle_db_error
def add_activity_log(
    event_type: str,
    description: str,
    severity: str = "info",
    user_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[str] = None
) -> None:
    """Add a new activity log entry to the SQL Server database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO activity_log (event_type, description, severity, user_id, source, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_type, description, severity, user_id, source, metadata))
            conn.commit()
            cursor.close()
            
        # Broadcast via WebSocket to live clients
        try:
            from app.core.websocket import manager
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast_activity_update({
                        "event_type": event_type,
                        "description": description,
                        "severity": severity,
                        "created_at": datetime.now().isoformat(),
                        "user": user_id,
                        "source": source,
                        "metadata": metadata
                    }))
            except RuntimeError:
                pass
        except Exception:
            pass
            
    except Exception as e:
        logger.error(f"Failed to write activity log: {e}")
