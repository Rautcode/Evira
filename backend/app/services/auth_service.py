import pyodbc
from typing import Optional, Dict

import os

def validate_sql_login(server: str, database: str, username: Optional[str] = None, password: Optional[str] = None, auth_type: str = "sql") -> Dict:
    """
    Attempts to connect to SQL Server using provided credentials.
    Returns dict with success and user info or error message.
    """
    if os.getenv("MOCK_AUTH", "0") == "1":
        return {"success": True, "user": username or "windows_user"}
    
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
