"""SQLAlchemy models for durable Phase 2 storage.

ORM models are persistence mappings only. API DTOs remain generated from
packages/contracts JSON Schema.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID as PyUUID

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from live_demo_api.db.base import Base
from live_demo_api.db.types import (
    ArtifactKind,
    BrowserSessionStatus,
    CrmExportStatus,
    DemoPhase,
    EventOutboxStatus,
    InsightType,
    ModelInvocationPurpose,
    PolicyDecision,
    ProductGuidanceType,
    RecipeStatus,
    RiskLevel,
    SessionStatus,
    TranscriptChunkType,
    TranscriptSpeaker,
    UserRole,
    check_values,
)


def uuid_pk(name: str) -> Mapped[PyUUID]:
    return mapped_column(
        name,
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def created_at_column() -> Mapped[datetime]:
    return mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def updated_at_column() -> Mapped[datetime]:
    return mapped_column(sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = (sa.Index("ix_organizations_deleted_at", "deleted_at"),)

    organization_id: Mapped[PyUUID] = uuid_pk("organization_id")
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    slug: Mapped[str] = mapped_column(sa.Text, nullable=False, unique=True)
    plan: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="free")
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    users: Mapped[list[User]] = relationship(back_populates="organization", lazy="raise")
    products: Mapped[list[Product]] = relationship(back_populates="organization", lazy="raise")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        sa.CheckConstraint(f"role IN ({check_values(UserRole)})", name="user_role"),
        sa.Index(
            "uq_users_organization_id_lower_email",
            "organization_id",
            sa.text("lower(email)"),
            unique=True,
        ),
        sa.Index("ix_users_organization_id_role", "organization_id", "role"),
        sa.Index("ix_users_organization_id_deleted_at", "organization_id", "deleted_at"),
    )

    user_id: Mapped[PyUUID] = uuid_pk("user_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    email: Mapped[str] = mapped_column(sa.Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(sa.Text)
    role: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default=UserRole.VIEWER.value)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(back_populates="users", lazy="raise")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="products_confidence_range"),
        sa.CheckConstraint("length(product_url) > 0", name="products_product_url_non_empty"),
        sa.CheckConstraint(
            "jsonb_typeof(configuration) = 'object'", name="products_configuration_object"
        ),
        sa.Index("ix_products_organization_id_deleted_at", "organization_id", "deleted_at"),
        sa.Index("ix_products_organization_id_product_url", "organization_id", "product_url"),
        sa.Index("ix_products_organization_id_product_name", "organization_id", "product_name"),
        sa.Index(
            "ix_products_organization_id_created_at_product_id",
            "organization_id",
            sa.text("created_at DESC"),
            sa.text("product_id DESC"),
        ),
    )

    product_id: Mapped[PyUUID] = uuid_pk("product_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    product_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    default_persona: Mapped[str | None] = mapped_column(sa.Text)
    product_summary: Mapped[str | None] = mapped_column(sa.Text)
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    configuration: Mapped[dict[str, object]] = mapped_column(
        JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(back_populates="products", lazy="raise")


class ProductGuidance(Base):
    __tablename__ = "product_guidance"
    __table_args__ = (
        sa.CheckConstraint(
            f"guidance_type IN ({check_values(ProductGuidanceType)})",
            name="product_guidance_guidance_type",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(content) = 'object'", name="product_guidance_content_object"
        ),
        sa.Index("ix_product_guidance_product_id_guidance_type", "product_id", "guidance_type"),
        sa.Index("ix_product_guidance_organization_id_product_id", "organization_id", "product_id"),
    )

    guidance_id: Mapped[PyUUID] = uuid_pk("guidance_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    guidance_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    title: Mapped[str | None] = mapped_column(sa.Text)
    content: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    source_uri: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.user_id")
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class DemoRecipe(Base):
    __tablename__ = "demo_recipes"
    __table_args__ = (
        sa.CheckConstraint(f"status IN ({check_values(RecipeStatus)})", name="demo_recipes_status"),
        sa.Index("ix_demo_recipes_product_id_is_active", "product_id", "is_active"),
        sa.Index(
            "ix_demo_recipes_organization_id_product_id_status",
            "organization_id",
            "product_id",
            "status",
        ),
        sa.Index(
            "uq_active_recipe_per_product_persona",
            "product_id",
            sa.text("COALESCE(target_persona, '')"),
            unique=True,
            postgresql_where=sa.text("is_active = true AND deleted_at IS NULL"),
        ),
    )

    recipe_id: Mapped[PyUUID] = uuid_pk("recipe_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    recipe_name: Mapped[str] = mapped_column(sa.Text, nullable=False)
    target_persona: Mapped[str | None] = mapped_column(sa.Text)
    demo_goal: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=RecipeStatus.DRAFT.value
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.false())
    never_click: Mapped[list[str]] = mapped_column(
        ARRAY(sa.Text), nullable=False, server_default=sa.text("'{}'::text[]")
    )
    global_talk_track: Mapped[str | None] = mapped_column(sa.Text)
    created_by: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("users.user_id")
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class DemoStep(Base):
    __tablename__ = "demo_steps"
    __table_args__ = (
        sa.CheckConstraint("step_order >= 0", name="demo_steps_step_order_non_negative"),
        sa.UniqueConstraint("recipe_id", "step_order", name="uq_demo_steps_recipe_id_step_order"),
        sa.UniqueConstraint("recipe_id", "step_key", name="uq_demo_steps_recipe_id_step_key"),
        sa.Index("ix_demo_steps_recipe_id_deleted_at", "recipe_id", "deleted_at"),
    )

    step_id: Mapped[PyUUID] = uuid_pk("step_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    recipe_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_recipes.recipe_id"), nullable=False
    )
    step_order: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    step_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    goal: Mapped[str] = mapped_column(sa.Text, nullable=False)
    screen_hint: Mapped[str | None] = mapped_column(sa.Text)
    click_hint: Mapped[str | None] = mapped_column(sa.Text)
    talk_track: Mapped[str | None] = mapped_column(sa.Text)
    allowed_actions: Mapped[list[str]] = mapped_column(
        ARRAY(sa.Text), nullable=False, server_default=sa.text("'{}'::text[]")
    )
    success_criteria: Mapped[list[str]] = mapped_column(
        ARRAY(sa.Text), nullable=False, server_default=sa.text("'{}'::text[]")
    )
    fallback_strategy: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class DemoSession(Base):
    __tablename__ = "demo_sessions"
    __table_args__ = (
        sa.CheckConstraint(
            f"status IN ({check_values(SessionStatus)})", name="demo_sessions_status"
        ),
        sa.CheckConstraint(
            f"current_phase IN ({check_values(DemoPhase)})", name="demo_sessions_current_phase"
        ),
        sa.CheckConstraint(
            "ended_at IS NULL OR started_at IS NULL OR ended_at >= started_at",
            name="demo_sessions_ended_after_started",
        ),
        sa.Index(
            "ix_demo_sessions_organization_id_status_created_at",
            "organization_id",
            "status",
            sa.text("created_at DESC"),
        ),
        sa.Index(
            "ix_demo_sessions_organization_id_created_at_session_id",
            "organization_id",
            sa.text("created_at DESC"),
            sa.text("session_id DESC"),
        ),
        sa.Index(
            "ix_demo_sessions_product_id_created_at", "product_id", sa.text("created_at DESC")
        ),
        sa.Index("ix_demo_sessions_recipe_id_created_at", "recipe_id", sa.text("created_at DESC")),
        sa.Index("ix_demo_sessions_transport_session_id", "transport_session_id"),
    )

    session_id: Mapped[PyUUID] = uuid_pk("session_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    recipe_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_recipes.recipe_id")
    )
    status: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=SessionStatus.CREATED.value
    )
    current_phase: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=DemoPhase.CREATED.value
    )
    start_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    user_persona: Mapped[str | None] = mapped_column(sa.Text)
    user_company: Mapped[str | None] = mapped_column(sa.Text)
    user_display_name: Mapped[str | None] = mapped_column(sa.Text)
    user_email: Mapped[str | None] = mapped_column(sa.Text)
    transport_session_id: Mapped[str | None] = mapped_column(sa.Text)
    started_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class BrowserSession(Base):
    __tablename__ = "browser_sessions"
    __table_args__ = (
        sa.CheckConstraint(
            f"status IN ({check_values(BrowserSessionStatus)})",
            name="browser_sessions_status",
        ),
        sa.Index("ix_browser_sessions_session_id_status", "session_id", "status"),
        sa.Index("ix_browser_sessions_organization_id_status", "organization_id", "status"),
    )

    browser_session_id: Mapped[PyUUID] = uuid_pk("browser_session_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    browser_provider: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=BrowserSessionStatus.CREATED.value
    )
    current_url: Mapped[str | None] = mapped_column(sa.Text)
    current_screen_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey(
            "screen_snapshots.screen_id",
            name="fk_browser_sessions_current_screen_id_screen_snapshots",
            use_alter=True,
        ),
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    ended_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class ScreenSnapshot(Base):
    __tablename__ = "screen_snapshots"
    __table_args__ = (
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="screen_snapshots_confidence_range"
        ),
        sa.Index("ix_screen_snapshots_product_id_screen_hash", "product_id", "screen_hash"),
        sa.Index(
            "ix_screen_snapshots_session_id_created_at", "session_id", sa.text("created_at DESC")
        ),
        sa.Index(
            "ix_screen_snapshots_browser_session_id_created_at",
            "browser_session_id",
            sa.text("created_at DESC"),
        ),
        sa.Index("ix_screen_snapshots_product_id_url_path", "product_id", "url_path"),
    )

    screen_id: Mapped[PyUUID] = uuid_pk("screen_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id")
    )
    browser_session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("browser_sessions.browser_session_id")
    )
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    url_path: Mapped[str | None] = mapped_column(sa.Text)
    title: Mapped[str | None] = mapped_column(sa.Text)
    screen_hash: Mapped[str] = mapped_column(sa.Text, nullable=False)
    visible_text: Mapped[str | None] = mapped_column(sa.Text)
    accessibility_tree: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    dom_summary: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    screenshot_artifact_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    screenshot_uri: Mapped[str | None] = mapped_column(sa.Text)
    summary: Mapped[str | None] = mapped_column(sa.Text)
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    created_at: Mapped[datetime] = created_at_column()


class UIElement(Base):
    __tablename__ = "ui_elements"
    __table_args__ = (
        sa.CheckConstraint(
            f"risk_level IN ({check_values(RiskLevel)})", name="ui_elements_risk_level"
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ui_elements_confidence_range"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(bbox) = 'object' AND bbox ? 'x' AND bbox ? 'y' "
            "AND bbox ? 'width' AND bbox ? 'height'",
            name="ui_elements_bbox_shape",
        ),
        sa.UniqueConstraint("screen_id", "element_id", name="uq_ui_elements_screen_id_element_id"),
        sa.Index("ix_ui_elements_screen_id", "screen_id"),
        sa.Index("ix_ui_elements_screen_id_risk_level", "screen_id", "risk_level"),
        sa.Index("ix_ui_elements_element_fingerprint", "element_fingerprint"),
    )

    ui_element_id: Mapped[PyUUID] = uuid_pk("ui_element_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    screen_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("screen_snapshots.screen_id"), nullable=False
    )
    element_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    role: Mapped[str | None] = mapped_column(sa.Text)
    label: Mapped[str | None] = mapped_column(sa.Text)
    selector_hint: Mapped[str | None] = mapped_column(sa.Text)
    element_fingerprint: Mapped[str | None] = mapped_column(sa.Text)
    bbox: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    visible: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    enabled: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    risk_level: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=RiskLevel.UNKNOWN.value
    )
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    created_at: Mapped[datetime] = created_at_column()


class DemoGraphEdge(Base):
    __tablename__ = "demo_graph_edges"
    __table_args__ = (
        sa.CheckConstraint(
            f"risk_level IN ({check_values(RiskLevel)})", name="demo_graph_edges_risk_level"
        ),
        sa.CheckConstraint(
            "success_count >= 0", name="demo_graph_edges_success_count_non_negative"
        ),
        sa.CheckConstraint(
            "failure_count >= 0", name="demo_graph_edges_failure_count_non_negative"
        ),
        sa.CheckConstraint(
            "average_latency_ms IS NULL OR average_latency_ms >= 0",
            name="demo_graph_edges_average_latency_non_negative",
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="demo_graph_edges_confidence_range"
        ),
        sa.Index("ix_demo_graph_edges_product_id_from_screen_id", "product_id", "from_screen_id"),
        sa.Index(
            "ix_demo_graph_edges_product_id_element_fingerprint",
            "product_id",
            "element_fingerprint",
        ),
        sa.Index(
            "ix_demo_graph_edges_product_id_confidence", "product_id", sa.text("confidence DESC")
        ),
    )

    edge_id: Mapped[PyUUID] = uuid_pk("edge_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    from_screen_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("screen_snapshots.screen_id")
    )
    to_screen_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("screen_snapshots.screen_id")
    )
    action_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    action_label: Mapped[str | None] = mapped_column(sa.Text)
    element_fingerprint: Mapped[str | None] = mapped_column(sa.Text)
    risk_level: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=RiskLevel.UNKNOWN.value
    )
    success_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="0")
    failure_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="0")
    average_latency_ms: Mapped[int | None] = mapped_column(sa.Integer)
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class TranscriptEvent(Base):
    __tablename__ = "transcript_events"
    __table_args__ = (
        sa.CheckConstraint(
            f"speaker IN ({check_values(TranscriptSpeaker)})",
            name="transcript_events_speaker",
        ),
        sa.CheckConstraint(
            f"chunk_type IN ({check_values(TranscriptChunkType)})",
            name="transcript_events_chunk_type",
        ),
        sa.CheckConstraint(
            "start_ms IS NULL OR start_ms >= 0", name="transcript_events_start_ms_non_negative"
        ),
        sa.CheckConstraint(
            "end_ms IS NULL OR end_ms >= 0", name="transcript_events_end_ms_non_negative"
        ),
        sa.CheckConstraint(
            "end_ms IS NULL OR start_ms IS NULL OR end_ms >= start_ms",
            name="transcript_events_end_after_start",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="transcript_events_confidence_range",
        ),
        sa.Index("ix_transcript_events_session_id_created_at", "session_id", "created_at"),
        sa.Index(
            "ix_transcript_events_session_id_speaker_created_at",
            "session_id",
            "speaker",
            "created_at",
        ),
        sa.Index(
            "ix_transcript_events_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
    )

    transcript_event_id: Mapped[PyUUID] = uuid_pk("transcript_event_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    speaker: Mapped[str] = mapped_column(sa.Text, nullable=False)
    chunk_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    text: Mapped[str] = mapped_column(sa.Text, nullable=False)
    is_final: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, server_default=sa.true())
    start_ms: Mapped[int | None] = mapped_column(sa.Integer)
    end_ms: Mapped[int | None] = mapped_column(sa.Integer)
    confidence: Mapped[Decimal | None] = mapped_column(sa.Numeric(4, 3))
    turn_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = created_at_column()


class ActionEvent(Base):
    __tablename__ = "action_events"
    __table_args__ = (
        sa.CheckConstraint(
            f"risk_level IN ({check_values(RiskLevel)})", name="action_events_risk_level"
        ),
        sa.CheckConstraint(
            f"policy_decision IN ({check_values(PolicyDecision)})",
            name="action_events_policy_decision",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="action_events_latency_non_negative"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(action_payload) = 'object'", name="action_events_payload_object"
        ),
        sa.Index("ix_action_events_session_id_created_at", "session_id", "created_at"),
        sa.Index("ix_action_events_session_id_action_type", "session_id", "action_type"),
        sa.Index("ix_action_events_session_id_policy_decision", "session_id", "policy_decision"),
        sa.Index(
            "ix_action_events_browser_session_id_created_at",
            "browser_session_id",
            sa.text("created_at DESC"),
        ),
    )

    action_event_id: Mapped[PyUUID] = uuid_pk("action_event_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    turn_id: Mapped[PyUUID | None] = mapped_column(UUID(as_uuid=True))
    browser_session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("browser_sessions.browser_session_id")
    )
    action_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    action_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=RiskLevel.UNKNOWN.value
    )
    policy_decision: Mapped[str] = mapped_column(sa.Text, nullable=False)
    success: Mapped[bool | None] = mapped_column(sa.Boolean)
    error_code: Mapped[str | None] = mapped_column(sa.Text)
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    from_screen_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("screen_snapshots.screen_id")
    )
    to_screen_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("screen_snapshots.screen_id")
    )
    latency_ms: Mapped[int | None] = mapped_column(sa.Integer)
    created_at: Mapped[datetime] = created_at_column()


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        sa.CheckConstraint("length(content) > 0", name="knowledge_chunks_content_non_empty"),
        sa.CheckConstraint(
            "jsonb_typeof(metadata) = 'object'", name="knowledge_chunks_metadata_object"
        ),
        sa.UniqueConstraint(
            "product_id", "content_hash", name="uq_knowledge_chunks_product_id_content_hash"
        ),
        sa.Index("ix_knowledge_chunks_product_id_source_type", "product_id", "source_type"),
        sa.Index("ix_knowledge_chunks_organization_id_product_id", "organization_id", "product_id"),
    )

    chunk_id: Mapped[PyUUID] = uuid_pk("chunk_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    product_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    source_id: Mapped[str | None] = mapped_column(sa.Text)
    source_uri: Mapped[str | None] = mapped_column(sa.Text)
    title: Mapped[str | None] = mapped_column(sa.Text)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(sa.Text, nullable=False)
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class LeadInsight(Base):
    __tablename__ = "lead_insights"
    __table_args__ = (
        sa.CheckConstraint(
            f"insight_type IN ({check_values(InsightType)})", name="lead_insights_insight_type"
        ),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="lead_insights_confidence_range"
        ),
        sa.CheckConstraint("length(content) > 0", name="lead_insights_content_non_empty"),
        sa.CheckConstraint(
            "cardinality(evidence_transcript_event_ids) > 0 "
            "OR cardinality(evidence_browser_action_ids) > 0 "
            "OR cardinality(evidence_screen_ids) > 0 "
            "OR (insight_type = 'persona' AND confidence < 0.5)",
            name="lead_insights_evidence_required",
        ),
        sa.Index("ix_lead_insights_session_id_insight_type", "session_id", "insight_type"),
        sa.Index(
            "ix_lead_insights_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
    )

    insight_id: Mapped[PyUUID] = uuid_pk("insight_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    insight_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    evidence_transcript_event_ids: Mapped[list[PyUUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")
    )
    evidence_browser_action_ids: Mapped[list[PyUUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")
    )
    evidence_screen_ids: Mapped[list[PyUUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default=sa.text("'{}'::uuid[]")
    )
    created_at: Mapped[datetime] = created_at_column()


class LeadSummary(Base):
    __tablename__ = "lead_summaries"
    __table_args__ = (
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="lead_summaries_confidence_range"
        ),
        sa.CheckConstraint(
            "jsonb_typeof(summary) = 'object'", name="lead_summaries_summary_object"
        ),
        sa.UniqueConstraint("session_id", name="uq_lead_summaries_session_id"),
        sa.Index(
            "ix_lead_summaries_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
    )

    lead_summary_id: Mapped[PyUUID] = uuid_pk("lead_summary_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    summary: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    generated_by_provider: Mapped[str | None] = mapped_column(sa.Text)
    generated_by_model: Mapped[str | None] = mapped_column(sa.Text)
    confidence: Mapped[Decimal] = mapped_column(
        sa.Numeric(4, 3), nullable=False, server_default="0.000"
    )
    created_at: Mapped[datetime] = created_at_column()


class CrmExport(Base):
    __tablename__ = "crm_exports"
    __table_args__ = (
        sa.CheckConstraint(
            f"status IN ({check_values(CrmExportStatus)})", name="crm_exports_status"
        ),
        sa.CheckConstraint("jsonb_typeof(payload) = 'object'", name="crm_exports_payload_object"),
        sa.Index("ix_crm_exports_session_id_provider", "session_id", "provider"),
        sa.Index(
            "ix_crm_exports_organization_id_status_created_at",
            "organization_id",
            "status",
            sa.text("created_at DESC"),
        ),
    )

    crm_export_id: Mapped[PyUUID] = uuid_pk("crm_export_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id"), nullable=False
    )
    provider: Mapped[str] = mapped_column(sa.Text, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=CrmExportStatus.PENDING.value
    )
    external_object_id: Mapped[str | None] = mapped_column(sa.Text)
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = updated_at_column()


class ModelInvocation(Base):
    __tablename__ = "model_invocations"
    __table_args__ = (
        sa.CheckConstraint(
            f"purpose IN ({check_values(ModelInvocationPurpose)})",
            name="model_invocations_purpose",
        ),
        sa.CheckConstraint(
            "latency_ms IS NULL OR latency_ms >= 0", name="model_invocations_latency_non_negative"
        ),
        sa.CheckConstraint(
            "prompt_tokens IS NULL OR prompt_tokens >= 0",
            name="model_invocations_prompt_tokens_non_negative",
        ),
        sa.CheckConstraint(
            "completion_tokens IS NULL OR completion_tokens >= 0",
            name="model_invocations_completion_tokens_non_negative",
        ),
        sa.CheckConstraint(
            "cost_usd IS NULL OR cost_usd >= 0", name="model_invocations_cost_non_negative"
        ),
        sa.Index(
            "ix_model_invocations_session_id_created_at", "session_id", sa.text("created_at DESC")
        ),
        sa.Index(
            "ix_model_invocations_organization_id_purpose_created_at",
            "organization_id",
            "purpose",
            sa.text("created_at DESC"),
        ),
        sa.Index(
            "ix_model_invocations_provider_model_created_at",
            "provider",
            "model",
            sa.text("created_at DESC"),
        ),
    )

    invocation_id: Mapped[PyUUID] = uuid_pk("invocation_id")
    organization_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id")
    )
    session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id")
    )
    provider: Mapped[str] = mapped_column(sa.Text, nullable=False)
    model: Mapped[str] = mapped_column(sa.Text, nullable=False)
    purpose: Mapped[str] = mapped_column(sa.Text, nullable=False)
    input_hash: Mapped[str | None] = mapped_column(sa.Text)
    output_hash: Mapped[str | None] = mapped_column(sa.Text)
    latency_ms: Mapped[int | None] = mapped_column(sa.Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(sa.Integer)
    completion_tokens: Mapped[int | None] = mapped_column(sa.Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 6))
    success: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)
    error_code: Mapped[str | None] = mapped_column(sa.Text)
    error_message: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        sa.Index(
            "ix_audit_logs_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
        sa.Index(
            "ix_audit_logs_organization_id_actor", "organization_id", "actor_type", "actor_id"
        ),
        sa.Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    audit_log_id: Mapped[PyUUID] = uuid_pk("audit_log_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    actor_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(sa.Text)
    action: Mapped[str] = mapped_column(sa.Text, nullable=False)
    resource_type: Mapped[str | None] = mapped_column(sa.Text)
    resource_id: Mapped[str | None] = mapped_column(sa.Text)
    metadata_: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")
    )
    ip_address: Mapped[str | None] = mapped_column(sa.Text)
    user_agent: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()


class ArtifactObject(Base):
    __tablename__ = "artifact_objects"
    __table_args__ = (
        sa.CheckConstraint(f"kind IN ({check_values(ArtifactKind)})", name="artifact_objects_kind"),
        sa.CheckConstraint(
            "size_bytes IS NULL OR size_bytes >= 0", name="artifact_objects_size_non_negative"
        ),
        sa.UniqueConstraint("bucket", "object_key", name="uq_artifact_objects_bucket_object_key"),
        sa.Index(
            "ix_artifact_objects_session_id_kind_created_at",
            "session_id",
            "kind",
            sa.text("created_at DESC"),
        ),
        sa.Index(
            "ix_artifact_objects_product_id_kind_created_at",
            "product_id",
            "kind",
            sa.text("created_at DESC"),
        ),
        sa.Index(
            "ix_artifact_objects_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
        sa.Index("ix_artifact_objects_retention_until", "retention_until"),
    )

    artifact_id: Mapped[PyUUID] = uuid_pk("artifact_id")
    organization_id: Mapped[PyUUID] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id"), nullable=False
    )
    session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id")
    )
    product_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("products.product_id")
    )
    kind: Mapped[str] = mapped_column(sa.Text, nullable=False)
    bucket: Mapped[str] = mapped_column(sa.Text, nullable=False)
    object_key: Mapped[str] = mapped_column(sa.Text, nullable=False)
    content_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(sa.BigInteger)
    sha256_hex: Mapped[str | None] = mapped_column(sa.Text)
    storage_provider: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="minio")
    pii_level: Mapped[str] = mapped_column(sa.Text, nullable=False, server_default="unknown")
    retention_until: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(sa.Text)
    created_at: Mapped[datetime] = created_at_column()
    deleted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))


class EventOutbox(Base):
    __tablename__ = "event_outbox"
    __table_args__ = (
        sa.CheckConstraint(
            f"status IN ({check_values(EventOutboxStatus)})", name="event_outbox_status"
        ),
        sa.CheckConstraint("attempt_count >= 0", name="event_outbox_attempt_count_non_negative"),
        sa.CheckConstraint("jsonb_typeof(payload) = 'object'", name="event_outbox_payload_object"),
        sa.UniqueConstraint("event_id", name="uq_event_outbox_event_id"),
        sa.Index("ix_event_outbox_status_available_at", "status", "available_at"),
        sa.Index("ix_event_outbox_session_id_created_at", "session_id", sa.text("created_at DESC")),
        sa.Index(
            "ix_event_outbox_organization_id_created_at",
            "organization_id",
            sa.text("created_at DESC"),
        ),
    )

    outbox_id: Mapped[PyUUID] = uuid_pk("outbox_id")
    organization_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("organizations.organization_id")
    )
    session_id: Mapped[PyUUID | None] = mapped_column(
        UUID(as_uuid=True), sa.ForeignKey("demo_sessions.session_id")
    )
    event_id: Mapped[PyUUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event_type: Mapped[str] = mapped_column(sa.Text, nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False)
    trace_id: Mapped[str] = mapped_column(sa.Text, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.Text, nullable=False, server_default=EventOutboxStatus.PENDING.value
    )
    attempt_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default="0")
    last_error: Mapped[str | None] = mapped_column(sa.Text)
    available_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    created_at: Mapped[datetime] = created_at_column()
    published_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))
