"""users table for simple app login

Adds an application users table so login is a simple username/password against
app accounts, decoupled from the SQL Server connection (which is configured in
Settings). The default admin is seeded at startup (see app.services.user_service).

Revision ID: 0003_users
Revises: 0002_tag_mapping_rules
Create Date: 2026-06-16
"""
from alembic import op

revision = "0003_users"
down_revision = "0002_tag_mapping_rules"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type = N'U')
        CREATE TABLE users (
            id INT IDENTITY(1,1) PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'operator',
            active BIT NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE()
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS users")
