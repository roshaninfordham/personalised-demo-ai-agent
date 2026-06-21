"""Phase 9 policy and audit hardening.

Revision ID: 0003_phase_9_policy_audit
Revises: 0002_phase_3_api_support
Create Date: 2026-06-20 00:00:02.000000
"""

from __future__ import annotations

from alembic import op

revision = "0003_phase_9_policy_audit"
down_revision = "0002_phase_3_api_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS session_id UUID NULL")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS risk_level TEXT NULL")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS policy_decision TEXT NULL")
    op.execute(
        """
        ALTER TABLE audit_logs
        ADD COLUMN IF NOT EXISTS reason_codes TEXT[] NOT NULL DEFAULT '{}'::text[]
        """
    )
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_id TEXT NULL")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS trace_id TEXT NULL")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS event_hash TEXT NULL")
    op.execute("ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS previous_event_hash TEXT NULL")
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_audit_logs_session_id'
          ) THEN
            ALTER TABLE audit_logs
            ADD CONSTRAINT fk_audit_logs_session_id
            FOREIGN KEY (session_id) REFERENCES demo_sessions(session_id);
          END IF;
        END $$;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_org_action_created
        ON audit_logs (organization_id, action, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_session
        ON audit_logs (session_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_logs are append-only';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_audit_log_update ON audit_logs;
        CREATE TRIGGER trg_prevent_audit_log_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_audit_log_delete ON audit_logs;
        CREATE TRIGGER trg_prevent_audit_log_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_log_delete ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_log_update ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS prevent_audit_log_modification()")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_session")
    op.execute("DROP INDEX IF EXISTS ix_audit_logs_org_action_created")
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS fk_audit_logs_session_id")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS previous_event_hash")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS event_hash")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS trace_id")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS request_id")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS reason_codes")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS policy_decision")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS risk_level")
    op.execute("ALTER TABLE audit_logs DROP COLUMN IF EXISTS session_id")
