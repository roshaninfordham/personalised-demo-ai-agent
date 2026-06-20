"""Initial durable storage schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-20 00:00:00.000000
"""

from __future__ import annotations

# ruff: noqa: E501
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


MUTABLE_TABLES = (
    "organizations",
    "users",
    "products",
    "product_guidance",
    "demo_recipes",
    "demo_steps",
    "demo_sessions",
    "browser_sessions",
    "demo_graph_edges",
    "knowledge_chunks",
    "crm_exports",
)


def _create_updated_at_trigger(table_name: str) -> None:
    op.execute(
        f"""
        CREATE TRIGGER trg_{table_name}_set_updated_at
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at()
        """
    )


def _drop_updated_at_trigger(table_name: str) -> None:
    op.execute(f"DROP TRIGGER IF EXISTS trg_{table_name}_set_updated_at ON {table_name}")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = now();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    op.execute(
        """
        CREATE TABLE organizations (
          organization_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name TEXT NOT NULL,
          slug TEXT NOT NULL UNIQUE,
          plan TEXT NOT NULL DEFAULT 'free',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL
        )
        """
    )
    op.execute("CREATE INDEX ix_organizations_deleted_at ON organizations (deleted_at)")

    op.execute(
        """
        CREATE TABLE users (
          user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          email TEXT NOT NULL,
          display_name TEXT NULL,
          role TEXT NOT NULL DEFAULT 'viewer',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_users_user_role
            CHECK (role IN ('owner', 'admin', 'demo_builder', 'viewer', 'agent_runtime'))
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_users_organization_id_lower_email ON users (organization_id, lower(email))"
    )
    op.execute("CREATE INDEX ix_users_organization_id_role ON users (organization_id, role)")
    op.execute(
        "CREATE INDEX ix_users_organization_id_deleted_at ON users (organization_id, deleted_at)"
    )

    op.execute(
        """
        CREATE TABLE products (
          product_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_name TEXT NOT NULL,
          product_url TEXT NOT NULL,
          default_persona TEXT NULL,
          product_summary TEXT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_products_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT ck_products_product_url_non_empty CHECK (length(product_url) > 0)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_products_organization_id_deleted_at ON products (organization_id, deleted_at)"
    )
    op.execute(
        "CREATE INDEX ix_products_organization_id_product_url ON products (organization_id, product_url)"
    )
    op.execute(
        "CREATE INDEX ix_products_organization_id_product_name ON products (organization_id, product_name)"
    )

    op.execute(
        """
        CREATE TABLE product_guidance (
          guidance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          guidance_type TEXT NOT NULL,
          title TEXT NULL,
          content JSONB NOT NULL,
          source_uri TEXT NULL,
          created_by UUID NULL REFERENCES users(user_id),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_product_guidance_guidance_type CHECK (
            guidance_type IN (
              'text', 'document', 'recipe', 'recording', 'objection_playbook',
              'messaging', 'sales_script'
            )
          ),
          CONSTRAINT ck_product_guidance_content_object CHECK (jsonb_typeof(content) = 'object')
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_product_guidance_product_id_guidance_type ON product_guidance (product_id, guidance_type)"
    )
    op.execute(
        "CREATE INDEX ix_product_guidance_organization_id_product_id ON product_guidance (organization_id, product_id)"
    )

    op.execute(
        """
        CREATE TABLE demo_recipes (
          recipe_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          recipe_name TEXT NOT NULL,
          target_persona TEXT NULL,
          demo_goal TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'draft',
          is_active BOOLEAN NOT NULL DEFAULT false,
          never_click TEXT[] NOT NULL DEFAULT '{}',
          global_talk_track TEXT NULL,
          created_by UUID NULL REFERENCES users(user_id),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_demo_recipes_status CHECK (status IN ('draft', 'active', 'archived'))
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_demo_recipes_product_id_is_active ON demo_recipes (product_id, is_active)"
    )
    op.execute(
        "CREATE INDEX ix_demo_recipes_organization_id_product_id_status ON demo_recipes (organization_id, product_id, status)"
    )
    op.execute(
        """
        CREATE UNIQUE INDEX uq_active_recipe_per_product_persona
        ON demo_recipes (product_id, COALESCE(target_persona, ''))
        WHERE is_active = true AND deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE TABLE demo_steps (
          step_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          recipe_id UUID NOT NULL REFERENCES demo_recipes(recipe_id),
          step_order INTEGER NOT NULL,
          step_key TEXT NOT NULL,
          goal TEXT NOT NULL,
          screen_hint TEXT NULL,
          click_hint TEXT NULL,
          talk_track TEXT NULL,
          allowed_actions TEXT[] NOT NULL DEFAULT '{}',
          success_criteria TEXT[] NOT NULL DEFAULT '{}',
          fallback_strategy TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_demo_steps_step_order_non_negative CHECK (step_order >= 0),
          CONSTRAINT uq_demo_steps_recipe_id_step_order UNIQUE (recipe_id, step_order),
          CONSTRAINT uq_demo_steps_recipe_id_step_key UNIQUE (recipe_id, step_key)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_demo_steps_recipe_id_deleted_at ON demo_steps (recipe_id, deleted_at)"
    )

    op.execute(
        """
        CREATE TABLE demo_sessions (
          session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          recipe_id UUID NULL REFERENCES demo_recipes(recipe_id),
          status TEXT NOT NULL DEFAULT 'created',
          current_phase TEXT NOT NULL DEFAULT 'created',
          start_url TEXT NOT NULL,
          user_persona TEXT NULL,
          user_company TEXT NULL,
          user_display_name TEXT NULL,
          user_email TEXT NULL,
          transport_session_id TEXT NULL,
          started_at TIMESTAMPTZ NULL,
          ended_at TIMESTAMPTZ NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_demo_sessions_status CHECK (
            status IN ('created', 'prewarming', 'waiting_for_user', 'live', 'ending', 'completed', 'failed')
          ),
          CONSTRAINT ck_demo_sessions_current_phase CHECK (
            current_phase IN (
              'created', 'prewarming', 'discovery', 'overview', 'core_workflow',
              'deep_dive', 'q_and_a', 'summary', 'recovery', 'completed', 'failed'
            )
          ),
          CONSTRAINT ck_demo_sessions_ended_after_started
            CHECK (ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_demo_sessions_organization_id_status_created_at ON demo_sessions (organization_id, status, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_demo_sessions_product_id_created_at ON demo_sessions (product_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_demo_sessions_recipe_id_created_at ON demo_sessions (recipe_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_demo_sessions_transport_session_id ON demo_sessions (transport_session_id)"
    )

    op.execute(
        """
        CREATE TABLE browser_sessions (
          browser_session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          browser_provider TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'created',
          current_url TEXT NULL,
          current_screen_id UUID NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          ended_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_browser_sessions_status CHECK (
            status IN ('created', 'starting', 'ready', 'navigating', 'active', 'closing', 'closed', 'failed')
          )
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_browser_sessions_session_id_status ON browser_sessions (session_id, status)"
    )
    op.execute(
        "CREATE INDEX ix_browser_sessions_organization_id_status ON browser_sessions (organization_id, status)"
    )

    op.execute(
        """
        CREATE TABLE screen_snapshots (
          screen_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          session_id UUID NULL REFERENCES demo_sessions(session_id),
          browser_session_id UUID NULL REFERENCES browser_sessions(browser_session_id),
          url TEXT NOT NULL,
          url_path TEXT NULL,
          title TEXT NULL,
          screen_hash TEXT NOT NULL,
          visible_text TEXT NULL,
          accessibility_tree JSONB NULL,
          dom_summary JSONB NULL,
          screenshot_artifact_id UUID NULL,
          screenshot_uri TEXT NULL,
          summary TEXT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_screen_snapshots_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_screen_snapshots_product_id_screen_hash ON screen_snapshots (product_id, screen_hash)"
    )
    op.execute(
        "CREATE INDEX ix_screen_snapshots_session_id_created_at ON screen_snapshots (session_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_screen_snapshots_browser_session_id_created_at ON screen_snapshots (browser_session_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_screen_snapshots_product_id_url_path ON screen_snapshots (product_id, url_path)"
    )
    op.execute(
        """
        ALTER TABLE browser_sessions
        ADD CONSTRAINT fk_browser_sessions_current_screen_id_screen_snapshots
        FOREIGN KEY (current_screen_id) REFERENCES screen_snapshots(screen_id)
        """
    )

    op.execute(
        """
        CREATE TABLE ui_elements (
          ui_element_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          screen_id UUID NOT NULL REFERENCES screen_snapshots(screen_id),
          element_id TEXT NOT NULL,
          role TEXT NULL,
          label TEXT NULL,
          selector_hint TEXT NULL,
          element_fingerprint TEXT NULL,
          bbox JSONB NOT NULL,
          visible BOOLEAN NOT NULL DEFAULT true,
          enabled BOOLEAN NOT NULL DEFAULT true,
          risk_level TEXT NOT NULL DEFAULT 'unknown',
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_ui_elements_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'blocked', 'unknown')),
          CONSTRAINT ck_ui_elements_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT ck_ui_elements_bbox_shape CHECK (
            jsonb_typeof(bbox) = 'object'
            AND bbox ? 'x'
            AND bbox ? 'y'
            AND bbox ? 'width'
            AND bbox ? 'height'
          ),
          CONSTRAINT uq_ui_elements_screen_id_element_id UNIQUE (screen_id, element_id)
        )
        """
    )
    op.execute("CREATE INDEX ix_ui_elements_screen_id ON ui_elements (screen_id)")
    op.execute(
        "CREATE INDEX ix_ui_elements_screen_id_risk_level ON ui_elements (screen_id, risk_level)"
    )
    op.execute(
        "CREATE INDEX ix_ui_elements_element_fingerprint ON ui_elements (element_fingerprint)"
    )

    op.execute(
        """
        CREATE TABLE demo_graph_edges (
          edge_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          from_screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          to_screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          action_type TEXT NOT NULL,
          action_label TEXT NULL,
          element_fingerprint TEXT NULL,
          risk_level TEXT NOT NULL DEFAULT 'unknown',
          success_count INTEGER NOT NULL DEFAULT 0,
          failure_count INTEGER NOT NULL DEFAULT 0,
          average_latency_ms INTEGER NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_demo_graph_edges_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'blocked', 'unknown')),
          CONSTRAINT ck_demo_graph_edges_success_count_non_negative CHECK (success_count >= 0),
          CONSTRAINT ck_demo_graph_edges_failure_count_non_negative CHECK (failure_count >= 0),
          CONSTRAINT ck_demo_graph_edges_average_latency_non_negative CHECK (average_latency_ms IS NULL OR average_latency_ms >= 0),
          CONSTRAINT ck_demo_graph_edges_confidence_range CHECK (confidence >= 0 AND confidence <= 1)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_demo_graph_edges_product_id_from_screen_id ON demo_graph_edges (product_id, from_screen_id)"
    )
    op.execute(
        "CREATE INDEX ix_demo_graph_edges_product_id_element_fingerprint ON demo_graph_edges (product_id, element_fingerprint)"
    )
    op.execute(
        "CREATE INDEX ix_demo_graph_edges_product_id_confidence ON demo_graph_edges (product_id, confidence DESC)"
    )

    op.execute(
        """
        CREATE TABLE transcript_events (
          transcript_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          speaker TEXT NOT NULL,
          chunk_type TEXT NOT NULL,
          text TEXT NOT NULL,
          is_final BOOLEAN NOT NULL DEFAULT true,
          start_ms INTEGER NULL,
          end_ms INTEGER NULL,
          confidence NUMERIC(4,3) NULL,
          turn_id UUID NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_transcript_events_speaker CHECK (speaker IN ('user', 'assistant', 'system', 'tool')),
          CONSTRAINT ck_transcript_events_chunk_type CHECK (chunk_type IN ('partial', 'final', 'interrupted')),
          CONSTRAINT ck_transcript_events_start_ms_non_negative CHECK (start_ms IS NULL OR start_ms >= 0),
          CONSTRAINT ck_transcript_events_end_ms_non_negative CHECK (end_ms IS NULL OR end_ms >= 0),
          CONSTRAINT ck_transcript_events_end_after_start CHECK (end_ms IS NULL OR start_ms IS NULL OR end_ms >= start_ms),
          CONSTRAINT ck_transcript_events_confidence_range CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_transcript_events_session_id_created_at ON transcript_events (session_id, created_at)"
    )
    op.execute(
        "CREATE INDEX ix_transcript_events_session_id_speaker_created_at ON transcript_events (session_id, speaker, created_at)"
    )
    op.execute(
        "CREATE INDEX ix_transcript_events_organization_id_created_at ON transcript_events (organization_id, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE action_events (
          action_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          turn_id UUID NULL,
          browser_session_id UUID NULL REFERENCES browser_sessions(browser_session_id),
          action_type TEXT NOT NULL,
          action_payload JSONB NOT NULL,
          risk_level TEXT NOT NULL DEFAULT 'unknown',
          policy_decision TEXT NOT NULL,
          success BOOLEAN NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          from_screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          to_screen_id UUID NULL REFERENCES screen_snapshots(screen_id),
          latency_ms INTEGER NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_action_events_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'blocked', 'unknown')),
          CONSTRAINT ck_action_events_policy_decision CHECK (policy_decision IN ('allowed', 'blocked', 'confirmation_required')),
          CONSTRAINT ck_action_events_latency_non_negative CHECK (latency_ms IS NULL OR latency_ms >= 0),
          CONSTRAINT ck_action_events_payload_object CHECK (jsonb_typeof(action_payload) = 'object')
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_action_events_session_id_created_at ON action_events (session_id, created_at)"
    )
    op.execute(
        "CREATE INDEX ix_action_events_session_id_action_type ON action_events (session_id, action_type)"
    )
    op.execute(
        "CREATE INDEX ix_action_events_session_id_policy_decision ON action_events (session_id, policy_decision)"
    )
    op.execute(
        "CREATE INDEX ix_action_events_browser_session_id_created_at ON action_events (browser_session_id, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE knowledge_chunks (
          chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          product_id UUID NOT NULL REFERENCES products(product_id),
          source_type TEXT NOT NULL,
          source_id TEXT NULL,
          source_uri TEXT NULL,
          title TEXT NULL,
          content TEXT NOT NULL,
          content_hash TEXT NOT NULL,
          metadata JSONB NOT NULL DEFAULT '{}',
          embedding vector(768) NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_knowledge_chunks_content_non_empty CHECK (length(content) > 0),
          CONSTRAINT ck_knowledge_chunks_metadata_object CHECK (jsonb_typeof(metadata) = 'object'),
          CONSTRAINT uq_knowledge_chunks_product_id_content_hash UNIQUE (product_id, content_hash)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_product_id_source_type ON knowledge_chunks (product_id, source_type)"
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_organization_id_product_id ON knowledge_chunks (organization_id, product_id)"
    )
    op.execute(
        """
        CREATE INDEX ix_knowledge_chunks_embedding_hnsw
        ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE TABLE lead_insights (
          insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          insight_type TEXT NOT NULL,
          content TEXT NOT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          evidence_transcript_event_ids UUID[] NOT NULL DEFAULT '{}',
          evidence_browser_action_ids UUID[] NOT NULL DEFAULT '{}',
          evidence_screen_ids UUID[] NOT NULL DEFAULT '{}',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_lead_insights_insight_type CHECK (
            insight_type IN (
              'pain_point', 'use_case', 'objection', 'buying_signal',
              'question', 'feature_interest', 'persona', 'urgency'
            )
          ),
          CONSTRAINT ck_lead_insights_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT ck_lead_insights_content_non_empty CHECK (length(content) > 0),
          CONSTRAINT ck_lead_insights_evidence_required CHECK (
            cardinality(evidence_transcript_event_ids) > 0
            OR cardinality(evidence_browser_action_ids) > 0
            OR cardinality(evidence_screen_ids) > 0
            OR (insight_type = 'persona' AND confidence < 0.5)
          )
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_lead_insights_session_id_insight_type ON lead_insights (session_id, insight_type)"
    )
    op.execute(
        "CREATE INDEX ix_lead_insights_organization_id_created_at ON lead_insights (organization_id, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE lead_summaries (
          lead_summary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          summary JSONB NOT NULL,
          generated_by_provider TEXT NULL,
          generated_by_model TEXT NULL,
          confidence NUMERIC(4,3) NOT NULL DEFAULT 0.000,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_lead_summaries_confidence_range CHECK (confidence >= 0 AND confidence <= 1),
          CONSTRAINT ck_lead_summaries_summary_object CHECK (jsonb_typeof(summary) = 'object'),
          CONSTRAINT uq_lead_summaries_session_id UNIQUE (session_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_lead_summaries_organization_id_created_at ON lead_summaries (organization_id, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE crm_exports (
          crm_export_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NOT NULL REFERENCES demo_sessions(session_id),
          provider TEXT NOT NULL,
          payload JSONB NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          external_object_id TEXT NULL,
          error_message TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_crm_exports_status CHECK (status IN ('pending', 'sent', 'failed', 'skipped')),
          CONSTRAINT ck_crm_exports_payload_object CHECK (jsonb_typeof(payload) = 'object')
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_crm_exports_session_id_provider ON crm_exports (session_id, provider)"
    )
    op.execute(
        "CREATE INDEX ix_crm_exports_organization_id_status_created_at ON crm_exports (organization_id, status, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE model_invocations (
          invocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NULL REFERENCES organizations(organization_id),
          session_id UUID NULL REFERENCES demo_sessions(session_id),
          provider TEXT NOT NULL,
          model TEXT NOT NULL,
          purpose TEXT NOT NULL,
          input_hash TEXT NULL,
          output_hash TEXT NULL,
          latency_ms INTEGER NULL,
          prompt_tokens INTEGER NULL,
          completion_tokens INTEGER NULL,
          cost_usd NUMERIC(12,6) NULL,
          success BOOLEAN NOT NULL,
          error_code TEXT NULL,
          error_message TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT ck_model_invocations_purpose CHECK (
            purpose IN (
              'realtime_host', 'screen_summary', 'recipe_generation', 'lead_summary',
              'embedding', 'vision_fallback', 'safety_classification'
            )
          ),
          CONSTRAINT ck_model_invocations_latency_non_negative CHECK (latency_ms IS NULL OR latency_ms >= 0),
          CONSTRAINT ck_model_invocations_prompt_tokens_non_negative CHECK (prompt_tokens IS NULL OR prompt_tokens >= 0),
          CONSTRAINT ck_model_invocations_completion_tokens_non_negative CHECK (completion_tokens IS NULL OR completion_tokens >= 0),
          CONSTRAINT ck_model_invocations_cost_non_negative CHECK (cost_usd IS NULL OR cost_usd >= 0)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_model_invocations_session_id_created_at ON model_invocations (session_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_model_invocations_organization_id_purpose_created_at ON model_invocations (organization_id, purpose, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_model_invocations_provider_model_created_at ON model_invocations (provider, model, created_at DESC)"
    )

    op.execute(
        """
        CREATE TABLE audit_logs (
          audit_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          actor_type TEXT NOT NULL,
          actor_id TEXT NULL,
          action TEXT NOT NULL,
          resource_type TEXT NULL,
          resource_id TEXT NULL,
          metadata JSONB NOT NULL DEFAULT '{}',
          ip_address TEXT NULL,
          user_agent TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_audit_logs_organization_id_created_at ON audit_logs (organization_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_audit_logs_organization_id_actor ON audit_logs (organization_id, actor_type, actor_id)"
    )
    op.execute("CREATE INDEX ix_audit_logs_resource ON audit_logs (resource_type, resource_id)")

    op.execute(
        """
        CREATE TABLE artifact_objects (
          artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NOT NULL REFERENCES organizations(organization_id),
          session_id UUID NULL REFERENCES demo_sessions(session_id),
          product_id UUID NULL REFERENCES products(product_id),
          kind TEXT NOT NULL,
          bucket TEXT NOT NULL,
          object_key TEXT NOT NULL,
          content_type TEXT NOT NULL,
          size_bytes BIGINT NULL,
          sha256_hex TEXT NULL,
          storage_provider TEXT NOT NULL DEFAULT 'minio',
          pii_level TEXT NOT NULL DEFAULT 'unknown',
          retention_until TIMESTAMPTZ NULL,
          created_by TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_artifact_objects_kind CHECK (
            kind IN (
              'screenshot', 'recording', 'browser_trace', 'generated_report',
              'model_debug', 'transcript_export', 'other'
            )
          ),
          CONSTRAINT ck_artifact_objects_size_non_negative CHECK (size_bytes IS NULL OR size_bytes >= 0),
          CONSTRAINT uq_artifact_objects_bucket_object_key UNIQUE (bucket, object_key)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_artifact_objects_session_id_kind_created_at ON artifact_objects (session_id, kind, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_artifact_objects_product_id_kind_created_at ON artifact_objects (product_id, kind, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_artifact_objects_organization_id_created_at ON artifact_objects (organization_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_artifact_objects_retention_until ON artifact_objects (retention_until)"
    )
    op.execute(
        """
        ALTER TABLE screen_snapshots
        ADD CONSTRAINT fk_screen_snapshots_screenshot_artifact_id_artifact_objects
        FOREIGN KEY (screenshot_artifact_id) REFERENCES artifact_objects(artifact_id)
        """
    )

    op.execute(
        """
        CREATE TABLE event_outbox (
          outbox_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          organization_id UUID NULL REFERENCES organizations(organization_id),
          session_id UUID NULL REFERENCES demo_sessions(session_id),
          event_id UUID NOT NULL,
          event_type TEXT NOT NULL,
          payload JSONB NOT NULL,
          trace_id TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          attempt_count INTEGER NOT NULL DEFAULT 0,
          last_error TEXT NULL,
          available_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          published_at TIMESTAMPTZ NULL,
          CONSTRAINT ck_event_outbox_status CHECK (status IN ('pending', 'published', 'failed')),
          CONSTRAINT ck_event_outbox_attempt_count_non_negative CHECK (attempt_count >= 0),
          CONSTRAINT ck_event_outbox_payload_object CHECK (jsonb_typeof(payload) = 'object'),
          CONSTRAINT uq_event_outbox_event_id UNIQUE (event_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_event_outbox_status_available_at ON event_outbox (status, available_at)"
    )
    op.execute(
        "CREATE INDEX ix_event_outbox_session_id_created_at ON event_outbox (session_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_event_outbox_organization_id_created_at ON event_outbox (organization_id, created_at DESC)"
    )

    for table_name in MUTABLE_TABLES:
        _create_updated_at_trigger(table_name)


def downgrade() -> None:
    for table_name in reversed(MUTABLE_TABLES):
        _drop_updated_at_trigger(table_name)

    op.execute("DROP TABLE IF EXISTS event_outbox")
    op.execute(
        "ALTER TABLE screen_snapshots DROP CONSTRAINT IF EXISTS fk_screen_snapshots_screenshot_artifact_id_artifact_objects"
    )
    op.execute("DROP TABLE IF EXISTS artifact_objects")
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS model_invocations")
    op.execute("DROP TABLE IF EXISTS crm_exports")
    op.execute("DROP TABLE IF EXISTS lead_summaries")
    op.execute("DROP TABLE IF EXISTS lead_insights")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
    op.execute("DROP TABLE IF EXISTS action_events")
    op.execute("DROP TABLE IF EXISTS transcript_events")
    op.execute("DROP TABLE IF EXISTS demo_graph_edges")
    op.execute("DROP TABLE IF EXISTS ui_elements")
    op.execute(
        "ALTER TABLE browser_sessions DROP CONSTRAINT IF EXISTS fk_browser_sessions_current_screen_id_screen_snapshots"
    )
    op.execute("DROP TABLE IF EXISTS screen_snapshots")
    op.execute("DROP TABLE IF EXISTS browser_sessions")
    op.execute("DROP TABLE IF EXISTS demo_sessions")
    op.execute("DROP TABLE IF EXISTS demo_steps")
    op.execute("DROP TABLE IF EXISTS demo_recipes")
    op.execute("DROP TABLE IF EXISTS product_guidance")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS organizations")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
