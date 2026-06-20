from live_demo_api.db.base import Base
from live_demo_api.db.models import (
    ActionEvent,
    ArtifactObject,
    AuditLog,
    BrowserSession,
    CrmExport,
    DemoGraphEdge,
    DemoRecipe,
    DemoSession,
    DemoStep,
    EventOutbox,
    KnowledgeChunk,
    LeadInsight,
    LeadSummary,
    ModelInvocation,
    Organization,
    Product,
    ProductGuidance,
    ScreenSnapshot,
    TranscriptEvent,
    UIElement,
    User,
)


def test_required_tables_are_mapped() -> None:
    expected_tables = {
        "organizations",
        "users",
        "products",
        "product_guidance",
        "demo_recipes",
        "demo_steps",
        "demo_sessions",
        "browser_sessions",
        "screen_snapshots",
        "ui_elements",
        "demo_graph_edges",
        "transcript_events",
        "action_events",
        "knowledge_chunks",
        "lead_insights",
        "lead_summaries",
        "crm_exports",
        "model_invocations",
        "audit_logs",
        "artifact_objects",
        "event_outbox",
    }
    assert expected_tables.issubset(Base.metadata.tables)


def test_models_import_without_contract_dto_duplication() -> None:
    mapped_classes = [
        Organization,
        User,
        Product,
        ProductGuidance,
        DemoRecipe,
        DemoStep,
        DemoSession,
        BrowserSession,
        ScreenSnapshot,
        UIElement,
        DemoGraphEdge,
        TranscriptEvent,
        ActionEvent,
        KnowledgeChunk,
        LeadInsight,
        LeadSummary,
        CrmExport,
        ModelInvocation,
        AuditLog,
        ArtifactObject,
        EventOutbox,
    ]
    assert all(model.__tablename__ in Base.metadata.tables for model in mapped_classes)
