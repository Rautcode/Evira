"""Base error handling functionality."""

from app.utils.shared_utils import handle_db_error, add_activity_log

# Re-export the shared utilities
__all__ = ['handle_db_error', 'add_activity_log']