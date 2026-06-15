import pyodbc
from typing import Optional, Dict

import os


def _server_allowed(server: str) -> bool:
    """Restrict which DB servers the backend may connect to (anti-SSRF).

    Allowlist comes from MSSQL_ALLOWED_SERVERS (comma-separated); if unset it
    falls back to the configured MSSQL_SERVER. An explicit "*" disables the
    check (development only).
    """
    raw = os.getenv("MSSQL_ALLOWED_SERVERS") or os.getenv("MSSQL_SERVER", "")
    allowed = {s.strip().lower() for s in raw.split(",") if s.strip()}
    if "*" in allowed:
        return True
    # If nothing is configured, be permissive (single-tenant local dev) rather
    # than locking the operator out; production should set the allowlist.
    if not allowed:
        return True
    return (server or "").strip().lower() in allowed


def _has_connstr_injection(*values: Optional[str]) -> bool:
    """Reject values containing ODBC connection-string delimiters, which could
    inject extra connection attributes (e.g. username = 'x;Trusted_Connection=yes')."""
    return any(v is not None and any(c in v for c in (";", "{", "}", "\n", "\r")) for v in values)


def validate_sql_login(server: str, database: str, username: Optional[str] = None, password: Optional[str] = None, auth_type: str = "sql") -> Dict:
    """
    Attempts to connect to SQL Server using provided credentials.
    Returns dict with success and user info or error message.
    """
    if os.getenv("MOCK_AUTH", "0") == "1":
        return {"success": True, "user": username or "windows_user"}

    if not _server_allowed(server):
        return {"success": False, "error": "Database server is not in the allowed list"}

    if _has_connstr_injection(server, database, username, password):
        return {"success": False, "error": "Invalid characters in connection parameters"}

    try:
        if auth_type == "windows":
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
            )
            user = username or "windows_user"
        else:
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            )
            user = username
        conn.close()
        return {"success": True, "user": user}
    except Exception as e:
        return {"success": False, "error": str(e)}
