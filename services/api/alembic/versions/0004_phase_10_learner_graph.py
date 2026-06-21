"""Phase 10 learner runs, generated routes, and retrieval metadata.

Revision ID: 0004_phase_10_learner_graph
Revises: 0003_phase_9_policy_audit
Create Date: 2026-06-20 00:00:03.000000
"""

from __future__ import annotations

from alembic import op

revision = "0004_phase_10_learner_graph"
down_revision = "0003_phase_9_policy_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS product_learning_runs (
          learning_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          session_id UUID NULL REFERENCES demo_sessions(session_id),
          start_url TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          trigger_type TEXT NOT NULL,
          attempt_count INTEGER NOT NULL DEFAULT 0,
          max_attempts INTEGER NOT NULL DEFAULT 3,
          started_at TIMESTAMPTZ NULL,
          finished_at TIMESTAMPTZ NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT product_learning_runs_status
            CHECK (status IN ('pending','running','completed','failed','cancelled','dead_letter')),
          CONSTRAINT product_learning_runs_trigger_type
            CHECK (trigger_type IN ('product_created','session_created','manual','recipe_missing',
                                    'screen_unknown','scheduled_refresh')),
          CONSTRAINT product_learning_runs_attempt_non_negative CHECK (attempt_count >= 0),
          CONSTRAINT product_learning_runs_max_attempts_positive CHECK (max_attempts > 0),
          CONSTRAINT product_learning_runs_metrics_object CHECK (jsonb_typeof(metrics) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_product_learning_runs_org_status_created
        ON product_learning_runs(organization_id, status, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_product_learning_runs_product_created
        ON product_learning_runs(product_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_product_learning_runs_session_created
        ON product_learning_runs(session_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_demo_routes (
          route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          learning_run_id UUID NULL REFERENCES product_learning_runs(learning_run_id),
          route_name TEXT NOT NULL,
          route_type TEXT NOT NULL DEFAULT 'generated',
          target_persona TEXT NULL,
          status TEXT NOT NULL DEFAULT 'draft',
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          summary TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT generated_demo_routes_route_type
            CHECK (route_type IN ('generated','manual','hybrid')),
          CONSTRAINT generated_demo_routes_status
            CHECK (status IN ('draft','active','archived','invalid')),
          CONSTRAINT generated_demo_routes_confidence_range
            CHECK (confidence >= 0 AND confidence <= 1)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_generated_demo_routes_product_status
        ON generated_demo_routes(product_id, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_generated_demo_routes_product_confidence
        ON generated_demo_routes(product_id, confidence DESC)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS generated_demo_route_steps (
          route_step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          route_id UUID NOT NULL REFERENCES generated_demo_routes(route_id),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          step_order INTEGER NOT NULL,
          step_key TEXT NOT NULL,
          phase TEXT NOT NULL,
          goal TEXT NOT NULL,
          screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          recommended_action_id TEXT NULL,
          recommended_action_label TEXT NULL,
          talk_track TEXT NULL,
          fallback_strategy TEXT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT generated_demo_route_steps_order_non_negative CHECK (step_order >= 0),
          CONSTRAINT generated_demo_route_steps_confidence_range
            CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT generated_demo_route_steps_evidence_object
            CHECK (jsonb_typeof(evidence) = 'object'),
          CONSTRAINT uq_generated_demo_route_steps_order UNIQUE(route_id, step_order),
          CONSTRAINT uq_generated_demo_route_steps_key UNIQUE(route_id, step_key)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS screen_match_history (
          screen_match_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          source_screen_id UUID NOT NULL REFERENCES screen_snapshots(screen_id),
          matched_screen_id UUID NOT NULL REFERENCES screen_snapshots(screen_id),
          similarity_score NUMERIC(5,4) NOT NULL,
          match_features JSONB NOT NULL DEFAULT '{}'::jsonb,
          decision TEXT NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT screen_match_history_similarity_range
            CHECK (similarity_score >= 0 AND similarity_score <= 1),
          CONSTRAINT screen_match_history_decision
            CHECK (decision IN ('matched','possible_match','not_match','manual_override')),
          CONSTRAINT screen_match_history_match_features_object
            CHECK (jsonb_typeof(match_features) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_screen_match_history_product_source
        ON screen_match_history(product_id, source_screen_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_screen_match_history_product_score
        ON screen_match_history(product_id, similarity_score DESC)
        """
    )
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS search_vector TSVECTOR NULL")
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS chunk_type TEXT NULL")
    op.execute(
        """
        ALTER TABLE knowledge_chunks
        ADD COLUMN IF NOT EXISTS source_confidence NUMERIC(4,3) DEFAULT 0.000
        """
    )
    op.execute(
        """
        ALTER TABLE knowledge_chunks
        ADD COLUMN IF NOT EXISTS redaction_applied BOOLEAN NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_search_vector
        ON knowledge_chunks USING gin(search_vector)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_product_chunk_type
        ON knowledge_chunks(product_id, chunk_type)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_product_content_hash
        ON knowledge_chunks(product_id, content_hash)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_product_content_hash")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_product_chunk_type")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_search_vector")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS redaction_applied")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS source_confidence")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS chunk_type")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS search_vector")
    op.execute("DROP INDEX IF EXISTS ix_screen_match_history_product_score")
    op.execute("DROP INDEX IF EXISTS ix_screen_match_history_product_source")
    op.execute("DROP TABLE IF EXISTS screen_match_history")
    op.execute("DROP TABLE IF EXISTS generated_demo_route_steps")
    op.execute("DROP INDEX IF EXISTS ix_generated_demo_routes_product_confidence")
    op.execute("DROP INDEX IF EXISTS ix_generated_demo_routes_product_status")
    op.execute("DROP TABLE IF EXISTS generated_demo_routes")
    op.execute("DROP INDEX IF EXISTS ix_product_learning_runs_session_created")
    op.execute("DROP INDEX IF EXISTS ix_product_learning_runs_product_created")
    op.execute("DROP INDEX IF EXISTS ix_product_learning_runs_org_status_created")
    op.execute("DROP TABLE IF EXISTS product_learning_runs")
