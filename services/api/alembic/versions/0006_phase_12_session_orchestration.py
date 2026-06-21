"""Phase 12 end-to-end session orchestration.

Revision ID: 0006_phase_12_orchestration
Revises: 0005_phase_11_recipe_engine
Create Date: 2026-06-21 00:00:06.000000
"""

from __future__ import annotations

from alembic import op

revision = "0006_phase_12_orchestration"
down_revision = "0005_phase_11_recipe_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS session_orchestration_runs (
          orchestration_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          run_type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          attempt_count INTEGER NOT NULL DEFAULT 0,
          started_at TIMESTAMPTZ NULL,
          finished_at TIMESTAMPTZ NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
          trace_id TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT session_orchestration_runs_run_type
            CHECK (run_type IN ('prewarm','live_start','recovery','shutdown','finalization')),
          CONSTRAINT session_orchestration_runs_status
            CHECK (
              status IN (
                'pending',
                'running',
                'completed',
                'completed_with_warnings',
                'failed',
                'cancelled'
              )
            ),
          CONSTRAINT session_orchestration_runs_attempt_non_negative
            CHECK (attempt_count >= 0),
          CONSTRAINT session_orchestration_runs_metrics_object
            CHECK (jsonb_typeof(metrics) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_session_orchestration_runs_session_created
        ON session_orchestration_runs(session_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_session_orchestration_runs_org_status
        ON session_orchestration_runs(organization_id, status, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS session_resource_allocations (
          resource_allocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          resource_type TEXT NOT NULL,
          resource_id TEXT NOT NULL,
          provider TEXT NULL,
          status TEXT NOT NULL DEFAULT 'allocated',
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          released_at TIMESTAMPTZ NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          CONSTRAINT session_resource_allocations_resource_type
            CHECK (
              resource_type IN (
                'browser_session',
                'voice_session',
                'transport_session',
                'learner_run',
                'compiled_recipe',
                'object_artifact',
                'redis_live_state'
              )
            ),
          CONSTRAINT session_resource_allocations_status
            CHECK (
              status IN (
                'allocating',
                'allocated',
                'ready',
                'failed',
                'releasing',
                'released',
                'release_failed'
              )
            ),
          CONSTRAINT session_resource_allocations_metadata_object
            CHECK (jsonb_typeof(metadata) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_session_resource_allocations_session_status
        ON session_resource_allocations(session_id, status)
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_session_resource_type_provider_active
        ON session_resource_allocations(session_id, resource_type, provider)
        WHERE status IN ('allocating', 'allocated', 'ready', 'releasing')
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS session_lifecycle_events (
          session_lifecycle_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          event_type TEXT NOT NULL,
          previous_status TEXT NULL,
          next_status TEXT NULL,
          resource_type TEXT NULL,
          resource_id TEXT NULL,
          severity TEXT NOT NULL DEFAULT 'info',
          message TEXT NULL,
          metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
          trace_id TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT session_lifecycle_events_severity
            CHECK (severity IN ('debug','info','warning','error')),
          CONSTRAINT session_lifecycle_events_metadata_object
            CHECK (jsonb_typeof(metadata) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_session_lifecycle_events_session_created
        ON session_lifecycle_events(session_id, created_at ASC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_session_lifecycle_events_org_created
        ON session_lifecycle_events(organization_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION prevent_session_lifecycle_event_modification()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'session_lifecycle_events are append-only';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'trg_prevent_session_lifecycle_event_update'
          ) THEN
            CREATE TRIGGER trg_prevent_session_lifecycle_event_update
            BEFORE UPDATE ON session_lifecycle_events
            FOR EACH ROW EXECUTE FUNCTION prevent_session_lifecycle_event_modification();
          END IF;
          IF NOT EXISTS (
            SELECT 1 FROM pg_trigger WHERE tgname = 'trg_prevent_session_lifecycle_event_delete'
          ) THEN
            CREATE TRIGGER trg_prevent_session_lifecycle_event_delete
            BEFORE DELETE ON session_lifecycle_events
            FOR EACH ROW EXECUTE FUNCTION prevent_session_lifecycle_event_modification();
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_session_lifecycle_event_delete
        ON session_lifecycle_events
        """
    )
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_prevent_session_lifecycle_event_update
        ON session_lifecycle_events
        """
    )
    op.execute("DROP FUNCTION IF EXISTS prevent_session_lifecycle_event_modification()")
    op.execute("DROP TABLE IF EXISTS session_lifecycle_events")
    op.execute("DROP TABLE IF EXISTS session_resource_allocations")
    op.execute("DROP TABLE IF EXISTS session_orchestration_runs")
