"""Shared utility functions for error handling and activity logging."""

import logging
from typing import Any, Callable, Optional
from functools import wraps
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

def handle_db_error(func: Callable) -> Callable:
    """Decorator to handle database errors."""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                raise
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                raise
        return sync_wrapper

def add_activity_log(
    event_type: str,
    description: str,
    severity: str = "info",
    user_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[str] = None
) -> None:
    """Add a new activity log entry."""
    logger.info(f"Activity Log - Type: {event_type}, Description: {description}, Severity: {severity}, User: {user_id}, Source: {source}, Metadata: {metadata}")
