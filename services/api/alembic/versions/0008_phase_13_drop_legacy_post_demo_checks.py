"""Drop legacy post-demo check constraints.

Revision ID: 0008_phase_13_legacy_checks
Revises: 0007_phase_13_post_demo
Create Date: 2026-06-21 00:00:08.000000
"""

from __future__ import annotations

from alembic import op

revision = "0008_phase_13_legacy_checks"
down_revision = "0007_phase_13_post_demo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS ck_lead_insights_insight_type")
    op.execute(
        "ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS ck_lead_insights_evidence_required"
    )
    op.execute("ALTER TABLE crm_exports DROP CONSTRAINT IF EXISTS ck_crm_exports_status")


def downgrade() -> None:
    pass
