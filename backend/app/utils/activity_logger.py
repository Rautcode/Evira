"""Activity logging utility functions."""

import pyodbc
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict, List
from app.utils.db_pool import get_db_connection
from app.utils.shared_utils import add_activity_log

logger = logging.getLogger(__name__)

def log_activity(
    event_type: str,
    description: str,
    severity: str = "info",
    user_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[str] = None
) -> None:
    """Log an activity event."""
    try:
        add_activity_log(
            event_type=event_type,
            description=description,
            severity=severity,
            user_id=user_id,
            source=source,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")
        raise RuntimeError(f"Failed to log activity: {e}") from e
