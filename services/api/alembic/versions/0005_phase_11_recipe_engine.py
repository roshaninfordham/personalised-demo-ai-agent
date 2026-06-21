"""Phase 11 compiled recipes, generation runs, and progress.

Revision ID: 0005_phase_11_recipe_engine
Revises: 0004_phase_10_learner_graph
Create Date: 2026-06-21 00:00:04.000000
"""

from __future__ import annotations

from alembic import op

revision = "0005_phase_11_recipe_engine"
down_revision = "0004_phase_10_learner_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS compiled_demo_recipes (
          compiled_recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          recipe_id UUID NOT NULL REFERENCES demo_recipes(recipe_id),
          recipe_version INTEGER NOT NULL DEFAULT 1,
          recipe_hash TEXT NOT NULL,
          compiled_hash TEXT NOT NULL,
          compiled_payload JSONB NOT NULL,
          status TEXT NOT NULL DEFAULT 'active',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT compiled_demo_recipes_status
            CHECK (status IN ('active','stale','invalid','archived')),
          CONSTRAINT uq_compiled_recipes_version UNIQUE(recipe_id, recipe_version),
          CONSTRAINT uq_compiled_recipes_hash UNIQUE(recipe_id, recipe_hash)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_compiled_demo_recipes_product_status
        ON compiled_demo_recipes(product_id, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_compiled_demo_recipes_recipe_status
        ON compiled_demo_recipes(recipe_id, status)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recipe_generation_runs (
          generation_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          source_guidance_id UUID NULL REFERENCES product_guidance(guidance_id),
          status TEXT NOT NULL DEFAULT 'pending',
          provider TEXT NULL,
          model TEXT NULL,
          input_hash TEXT NOT NULL,
          output_hash TEXT NULL,
          validation_passed BOOLEAN NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          finished_at TIMESTAMPTZ NULL,
          CONSTRAINT recipe_generation_runs_status
            CHECK (status IN ('pending','running','completed','failed','validation_failed'))
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recipe_generation_runs_product_created
        ON recipe_generation_runs(product_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recipe_generation_runs_org_status
        ON recipe_generation_runs(organization_id, status)
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS recipe_step_progress (
          recipe_step_progress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          recipe_id UUID NOT NULL REFERENCES demo_recipes(recipe_id),
          step_id UUID NOT NULL REFERENCES demo_steps(step_id),
          step_key TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          attempt_count INTEGER NOT NULL DEFAULT 0,
          matched_screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          matched_action_id TEXT NULL,
          matched_confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          started_at TIMESTAMPTZ NULL,
          completed_at TIMESTAMPTZ NULL,
          skipped_at TIMESTAMPTZ NULL,
          failed_at TIMESTAMPTZ NULL,
          adapted_from_step_id UUID NULL,
          failure_reason TEXT NULL,
          evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT recipe_step_progress_status
            CHECK (
              status IN (
                'pending',
                'in_progress',
                'completed',
                'skipped',
                'failed',
                'adapted',
                'blocked'
              )
            ),
          CONSTRAINT recipe_step_progress_attempt_non_negative CHECK (attempt_count >= 0),
          CONSTRAINT recipe_step_progress_confidence_range
            CHECK (matched_confidence >= 0 AND matched_confidence <= 1),
          CONSTRAINT recipe_step_progress_evidence_object CHECK (jsonb_typeof(evidence) = 'object'),
          CONSTRAINT uq_recipe_step_progress_session_step UNIQUE(session_id, step_id)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recipe_step_progress_session_status
        ON recipe_step_progress(session_id, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_recipe_step_progress_session_recipe
        ON recipe_step_progress(session_id, recipe_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_recipe_step_progress_session_recipe")
    op.execute("DROP INDEX IF EXISTS ix_recipe_step_progress_session_status")
    op.execute("DROP TABLE IF EXISTS recipe_step_progress")
    op.execute("DROP INDEX IF EXISTS ix_recipe_generation_runs_org_status")
    op.execute("DROP INDEX IF EXISTS ix_recipe_generation_runs_product_created")
    op.execute("DROP TABLE IF EXISTS recipe_generation_runs")
    op.execute("DROP INDEX IF EXISTS ix_compiled_demo_recipes_recipe_status")
    op.execute("DROP INDEX IF EXISTS ix_compiled_demo_recipes_product_status")
    op.execute("DROP TABLE IF EXISTS compiled_demo_recipes")
