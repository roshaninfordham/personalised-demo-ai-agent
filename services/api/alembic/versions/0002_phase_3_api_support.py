"""Phase 3 API support columns and indexes.

Revision ID: 0002_phase_3_api_support
Revises: 0001_initial_schema
Create Date: 2026-06-20 00:00:01.000000
"""

from __future__ import annotations

from alembic import op

revision = "0002_phase_3_api_support"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE products ADD COLUMN configuration JSONB NOT NULL DEFAULT '{}'::jsonb")
    op.execute(
        """
        ALTER TABLE products
        ADD CONSTRAINT ck_products_configuration_object
        CHECK (jsonb_typeof(configuration) = 'object')
        """
    )
    op.execute(
        """
        CREATE INDEX ix_products_organization_id_created_at_product_id
        ON products (organization_id, created_at DESC, product_id DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX ix_demo_sessions_organization_id_created_at_session_id
        ON demo_sessions (organization_id, created_at DESC, session_id DESC)
        """
    )
    op.execute("ALTER TABLE product_guidance DROP CONSTRAINT ck_product_guidance_guidance_type")
    op.execute(
        """
        ALTER TABLE product_guidance
        ADD CONSTRAINT ck_product_guidance_guidance_type CHECK (
          guidance_type IN (
            'text', 'document', 'recipe', 'recording', 'objection_playbook',
            'messaging', 'sales_script', 'product_positioning',
            'forbidden_actions', 'setup_notes'
          )
        )
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE product_guidance DROP CONSTRAINT ck_product_guidance_guidance_type")
    op.execute(
        """
        ALTER TABLE product_guidance
        ADD CONSTRAINT ck_product_guidance_guidance_type CHECK (
          guidance_type IN (
            'text', 'document', 'recipe', 'recording', 'objection_playbook',
            'messaging', 'sales_script'
          )
        )
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_demo_sessions_organization_id_created_at_session_id")
    op.execute("DROP INDEX IF EXISTS ix_products_organization_id_created_at_product_id")
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS ck_products_configuration_object")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS configuration")
