"""initial schema

Creates the full SCADA Reports schema (tables, indexes, stored procedures) by
running the project's known-good, idempotent SQL. Replaces the previous ad-hoc
raw-SQL init so the schema is now versioned and deterministic (DEFECTS D42).

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-15
"""
import os
import re
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

# SQL lives alongside the app utils; these files use idempotent IF NOT EXISTS
# guards and `GO` batch separators (a client directive, so we split on it).
SQL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../app/utils"))
SQL_FILES = ["init_db.sql", "update_db_tables.sql"]


def _execute_sql_file(fname: str) -> None:
    path = os.path.join(SQL_DIR, fname)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for batch in re.split(r"(?im)^\s*GO\s*$", content):
        batch = batch.strip()
        if batch:
            op.execute(batch)


def upgrade() -> None:
    for fname in SQL_FILES:
        _execute_sql_file(fname)


def downgrade() -> None:
    for stmt in (
        "DROP PROCEDURE IF EXISTS sp_get_scheduler_stats",
        "DROP PROCEDURE IF EXISTS sp_get_report_stats",
        "DROP PROCEDURE IF EXISTS sp_get_system_health",
        "DROP TABLE IF EXISTS logs",
        "DROP TABLE IF EXISTS Reports",
        "DROP TABLE IF EXISTS Machines",
        "DROP TABLE IF EXISTS system_health",
        "DROP TABLE IF EXISTS wincc_tags",
        "DROP TABLE IF EXISTS activity_log",
        "DROP TABLE IF EXISTS scheduled_tasks",
        "DROP TABLE IF EXISTS report_history",
    ):
        op.execute(stmt)
