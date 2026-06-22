"""Phase 13 post-demo intelligence.

Revision ID: 0007_phase_13_post_demo
Revises: 0006_phase_12_orchestration
Create Date: 2026-06-21 00:00:07.000000
"""

from __future__ import annotations

from alembic import op

revision = "0007_phase_13_post_demo"
down_revision = "0006_phase_12_orchestration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE lead_insights
        ADD COLUMN IF NOT EXISTS normalized_content_hash TEXT NOT NULL DEFAULT '',
        ADD COLUMN IF NOT EXISTS importance NUMERIC(4,3) NOT NULL DEFAULT 0.000,
        ADD COLUMN IF NOT EXISTS evidence_recipe_step_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],
        ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'post_demo',
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        """
    )
    op.execute("ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS lead_insights_insight_type")
    op.execute("ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS ck_lead_insights_insight_type")
    op.execute(
        """
        ALTER TABLE lead_insights
        ADD CONSTRAINT lead_insights_insight_type CHECK (
          insight_type IN (
            'pain_point',
            'use_case',
            'objection',
            'buying_signal',
            'question',
            'feature_interest',
            'persona',
            'role',
            'urgency',
            'unanswered_question',
            'decision_criteria',
            'next_step'
          )
        )
        """
    )
    op.execute(
        "ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS lead_insights_evidence_required"
    )
    op.execute(
        "ALTER TABLE lead_insights DROP CONSTRAINT IF EXISTS ck_lead_insights_evidence_required"
    )
    op.execute(
        """
        ALTER TABLE lead_insights
        ADD CONSTRAINT lead_insights_evidence_required CHECK (
          cardinality(evidence_transcript_event_ids) > 0
          OR cardinality(evidence_browser_action_ids) > 0
          OR cardinality(evidence_screen_ids) > 0
          OR cardinality(evidence_recipe_step_ids) > 0
          OR (insight_type = 'persona' AND confidence < 0.5)
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_insights_session_type_hash
        ON lead_insights(session_id, insight_type, normalized_content_hash)
        WHERE normalized_content_hash <> ''
        """
    )

    op.execute(
        """
        ALTER TABLE lead_summaries
        ADD COLUMN IF NOT EXISTS summary_version TEXT NOT NULL DEFAULT 'v1',
        ADD COLUMN IF NOT EXISTS generation_mode TEXT NOT NULL DEFAULT 'deterministic',
        ADD COLUMN IF NOT EXISTS evidence_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS redaction_applied BOOLEAN NOT NULL DEFAULT false,
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        """
    )

    op.execute(
        """
        ALTER TABLE crm_exports
        ADD COLUMN IF NOT EXISTS lead_summary_id UUID NULL
          REFERENCES lead_summaries(lead_summary_id),
        ADD COLUMN IF NOT EXISTS adapter_version TEXT NOT NULL DEFAULT 'v1',
        ADD COLUMN IF NOT EXISTS redacted_payload JSONB NULL,
        ADD COLUMN IF NOT EXISTS dry_run BOOLEAN NOT NULL DEFAULT true,
        ADD COLUMN IF NOT EXISTS external_object_ids JSONB NOT NULL DEFAULT '{}'::jsonb,
        ADD COLUMN IF NOT EXISTS idempotency_key TEXT NOT NULL DEFAULT '',
        ADD COLUMN IF NOT EXISTS error_code TEXT NULL,
        ADD COLUMN IF NOT EXISTS sent_at TIMESTAMPTZ NULL
        """
    )
    op.execute("ALTER TABLE crm_exports DROP CONSTRAINT IF EXISTS crm_exports_status")
    op.execute("ALTER TABLE crm_exports DROP CONSTRAINT IF EXISTS ck_crm_exports_status")
    op.execute(
        """
        ALTER TABLE crm_exports
        ADD CONSTRAINT crm_exports_status CHECK (
          status IN ('pending','validated','sent','failed','skipped','dry_run_completed')
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_exports_idempotency
        ON crm_exports(organization_id, provider, idempotency_key)
        WHERE idempotency_key <> ''
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS post_demo_jobs (
          post_demo_job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          job_type TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          attempt_count INTEGER NOT NULL DEFAULT 0,
          max_attempts INTEGER NOT NULL DEFAULT 3,
          idempotency_key TEXT NOT NULL,
          started_at TIMESTAMPTZ NULL,
          finished_at TIMESTAMPTZ NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
          trace_id TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT post_demo_jobs_type CHECK (
            job_type IN (
              'extract_lead_insights',
              'track_features_shown',
              'generate_lead_summary',
              'export_crm_payload',
              'run_full_post_demo_intelligence'
            )
          ),
          CONSTRAINT post_demo_jobs_status CHECK (
            status IN (
              'pending',
              'running',
              'completed',
              'completed_with_warnings',
              'failed',
              'dead_letter',
              'cancelled'
            )
          ),
          CONSTRAINT post_demo_jobs_attempt_non_negative CHECK (attempt_count >= 0),
          CONSTRAINT post_demo_jobs_max_attempts_positive CHECK (max_attempts > 0),
          CONSTRAINT post_demo_jobs_metrics_object CHECK (jsonb_typeof(metrics) = 'object'),
          CONSTRAINT uq_post_demo_jobs_idempotency
            UNIQUE(organization_id, session_id, job_type, idempotency_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_demo_jobs_status_created
        ON post_demo_jobs(status, created_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_demo_jobs_session_created
        ON post_demo_jobs(session_id, created_at DESC)
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS features_shown (
          feature_shown_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          feature_key TEXT NOT NULL,
          feature_label TEXT NOT NULL,
          feature_category TEXT NULL,
          source_type TEXT NOT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          evidence_transcript_event_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],
          evidence_browser_action_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],
          evidence_screen_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],
          evidence_recipe_step_ids UUID[] NOT NULL DEFAULT '{}'::uuid[],
          first_seen_at TIMESTAMPTZ NULL,
          last_seen_at TIMESTAMPTZ NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT features_shown_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT features_shown_key_non_empty CHECK (length(feature_key) > 0),
          CONSTRAINT features_shown_label_non_empty CHECK (length(feature_label) > 0),
          CONSTRAINT uq_features_shown_session_key UNIQUE(session_id, feature_key)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_features_shown_session_confidence
        ON features_shown(session_id, confidence DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_features_shown_product_feature
        ON features_shown(product_id, feature_key)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS features_shown")
    op.execute("DROP TABLE IF EXISTS post_demo_jobs")
    op.execute("DROP INDEX IF EXISTS uq_crm_exports_idempotency")
    op.execute("DROP INDEX IF EXISTS uq_lead_insights_session_type_hash")
