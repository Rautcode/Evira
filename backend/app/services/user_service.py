"""Application user accounts + password verification (argon2).

Login is a simple username/password against this table, independent of the SQL
Server connection used for data (that lives in Settings/env).
"""

import os
import logging
from typing import Optional, Dict, Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

from app.utils.db import get_db_connection

logger = logging.getLogger(__name__)
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Return the user dict if username/password are valid and active, else None."""
    if not username or not password:
        return None
    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT id, username, password_hash, role, active FROM users WHERE username = ?",
                username,
            )
            row = cur.fetchone()
        finally:
            cur.close()
    if not row or not row.active:
        return None
    try:
        _ph.verify(row.password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return None
    except Exception as e:
        logger.error(f"Password verify error for '{username}': {e}")
        return None
    return {"id": row.id, "username": row.username, "role": row.role}


def ensure_default_admin() -> None:
    """Seed a default admin account on first run (configurable via env)."""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT COUNT(*) FROM users")
                if cur.fetchone()[0] == 0:
                    cur.execute(
                        "INSERT INTO users (username, password_hash, role, active) VALUES (?, ?, 'admin', 1)",
                        username, hash_password(password),
                    )
                    conn.commit()
                    logger.info("Created default admin user '%s' (change the password!)", username)
            finally:
                cur.close()
    except Exception as e:
        logger.error(f"Failed to ensure default admin: {e}")
