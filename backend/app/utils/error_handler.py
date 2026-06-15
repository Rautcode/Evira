"""Database error handling utilities."""

from typing import Any, Callable
from functools import wraps
import logging
from app.utils.shared_utils import handle_db_error

logger = logging.getLogger(__name__)

# The handle_db_error decorator is now imported from shared_utils.py
