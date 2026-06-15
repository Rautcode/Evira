"""Programmatic Alembic migration runner.

The app uses raw pyodbc (no SQLAlchemy ORM models), so migrations are explicit
SQL revisions under ``migrations/versions``. This module builds the SQLAlchemy
URL from the same config the app uses and runs ``alembic upgrade head`` in-process
on startup.
"""

import os
import urllib.parse
import logging

from alembic.config import Config
from alembic import command
from app.utils.config_manager import config_manager

logger = logging.getLogger(__name__)

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ALEMBIC_INI = os.path.join(BACKEND_DIR, "alembic.ini")
MIGRATIONS_DIR = os.path.join(BACKEND_DIR, "migrations")

DRIVER = "ODBC Driver 17 for SQL Server"


def get_odbc_connection_string(database: str | None = None) -> str:
    """Build the ODBC connection string using the same precedence as DBConnector."""
    config = config_manager.load_config()
    server = config.get("mssql_server") or os.getenv("MSSQL_SERVER")
    database = database or config.get("mssql_database") or os.getenv("MSSQL_DATABASE", "scada_reports")
    auth_type = (config.get("mssql_auth_type") or os.getenv("MSSQL_AUTH_TYPE", "sql")).lower()
    if auth_type == "windows":
        return f"DRIVER={{{DRIVER}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
    username = config.get("mssql_username") or os.getenv("MSSQL_USERNAME")
    password = config.get("mssql_password") or os.getenv("MSSQL_PASSWORD")
    return f"DRIVER={{{DRIVER}}};SERVER={server};DATABASE={database};UID={username};PWD={password}"


def get_sqlalchemy_url(database: str | None = None) -> str:
    odbc = get_odbc_connection_string(database)
    return "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(odbc)


def _config() -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", MIGRATIONS_DIR)
    # Pass the URL via attributes, NOT set_main_option: the URL-encoded ODBC
    # string contains '%' which ConfigParser would treat as interpolation.
    cfg.attributes["sqlalchemy_url"] = get_sqlalchemy_url()
    return cfg


def run_migrations() -> None:
    """Apply all pending migrations (``alembic upgrade head``)."""
    command.upgrade(_config(), "head")
    logger.info("Alembic migrations applied (upgrade head).")
