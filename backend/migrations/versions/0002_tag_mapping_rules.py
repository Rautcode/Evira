"""tag mapping rules

Adds a configurable tag_mapping_rules table so OPC UA tag -> machine/parameter
mapping is no longer hardcoded. Seeds it with the previous heuristics so default
behavior is unchanged (DEFECTS D11 / SCADA onboarding).

Revision ID: 0002_tag_mapping_rules
Revises: 0001_initial_schema
Create Date: 2026-06-15
"""
from alembic import op

revision = "0002_tag_mapping_rules"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

# (match_text, machine_id) — order = priority
MACHINE_RULES = [
    ("extruder", "M001"), ("m001", "M001"),
    ("molding", "M002"), ("m002", "M002"),
    ("cooling", "M003"), ("chiller", "M003"), ("m003", "M003"),
    ("packaging", "M004"), ("m004", "M004"),
    ("mixer", "M005"), ("blending", "M005"), ("m005", "M005"),
]

# (match_text, parameter, unit) — order = priority
PARAMETER_RULES = [
    ("temperature", "Temperature", "C"), ("temp", "Temperature", "C"),
    ("pressure", "Pressure", "bar"), ("press", "Pressure", "bar"),
    ("speed", "Speed", "RPM"), ("rpm", "Speed", "RPM"),
    ("force", "Clamping Force", "kN"), ("clamp", "Clamping Force", "kN"),
    ("cycle", "Cycle Time", "s"), ("time", "Cycle Time", "s"),
    ("flow", "Flow Rate", "L/min"),
    ("count", "Pack Count", "pcs"), ("pack", "Pack Count", "pcs"),
    ("error", "Error Rate", "%"),
]


def upgrade() -> None:
    op.execute(
        """
        IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[tag_mapping_rules]') AND type = N'U')
        CREATE TABLE tag_mapping_rules (
            id INT IDENTITY(1,1) PRIMARY KEY,
            rule_type VARCHAR(20) NOT NULL,      -- 'machine' or 'parameter'
            match_text VARCHAR(100) NOT NULL,    -- case-insensitive substring
            machine_id VARCHAR(50) NULL,
            parameter VARCHAR(50) NULL,
            unit VARCHAR(20) NULL,
            priority INT NOT NULL DEFAULT 100,
            active BIT NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE()
        );
        """
    )
    # Seed defaults only if the table is empty (idempotent re-runs).
    for i, (match, machine) in enumerate(MACHINE_RULES):
        op.execute(
            "IF NOT EXISTS (SELECT 1 FROM tag_mapping_rules WHERE rule_type='machine' AND match_text='%s') "
            "INSERT INTO tag_mapping_rules (rule_type, match_text, machine_id, priority) "
            "VALUES ('machine', '%s', '%s', %d);" % (match, match, machine, i)
        )
    for i, (match, parameter, unit) in enumerate(PARAMETER_RULES):
        op.execute(
            "IF NOT EXISTS (SELECT 1 FROM tag_mapping_rules WHERE rule_type='parameter' AND match_text='%s') "
            "INSERT INTO tag_mapping_rules (rule_type, match_text, parameter, unit, priority) "
            "VALUES ('parameter', '%s', '%s', '%s', %d);" % (match, match, parameter, unit, i)
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tag_mapping_rules")
