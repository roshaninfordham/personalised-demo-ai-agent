"""Database enum values represented as TEXT plus CHECK constraints."""

from enum import StrEnum


class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    DEMO_BUILDER = "demo_builder"
    VIEWER = "viewer"
    AGENT_RUNTIME = "agent_runtime"


class ProductGuidanceType(StrEnum):
    TEXT = "text"
    DOCUMENT = "document"
    RECIPE = "recipe"
    RECORDING = "recording"
    OBJECTION_PLAYBOOK = "objection_playbook"
    MESSAGING = "messaging"
    SALES_SCRIPT = "sales_script"
    PRODUCT_POSITIONING = "product_positioning"
    FORBIDDEN_ACTIONS = "forbidden_actions"
    SETUP_NOTES = "setup_notes"


class RecipeStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class SessionStatus(StrEnum):
    CREATED = "created"
    PREWARMING = "prewarming"
    WAITING_FOR_USER = "waiting_for_user"
    LIVE = "live"
    ENDING = "ending"
    COMPLETED = "completed"
    FAILED = "failed"


class DemoPhase(StrEnum):
    CREATED = "created"
    PREWARMING = "prewarming"
    DISCOVERY = "discovery"
    OVERVIEW = "overview"
    CORE_WORKFLOW = "core_workflow"
    DEEP_DIVE = "deep_dive"
    Q_AND_A = "q_and_a"
    SUMMARY = "summary"
    RECOVERY = "recovery"
    COMPLETED = "completed"
    FAILED = "failed"


class BrowserSessionStatus(StrEnum):
    CREATED = "created"
    STARTING = "starting"
    READY = "ready"
    NAVIGATING = "navigating"
    ACTIVE = "active"
    CLOSING = "closing"
    CLOSED = "closed"
    FAILED = "failed"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class PolicyDecision(StrEnum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    CONFIRMATION_REQUIRED = "confirmation_required"


class TranscriptSpeaker(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class TranscriptChunkType(StrEnum):
    PARTIAL = "partial"
    FINAL = "final"
    INTERRUPTED = "interrupted"


class InsightType(StrEnum):
    PAIN_POINT = "pain_point"
    USE_CASE = "use_case"
    OBJECTION = "objection"
    BUYING_SIGNAL = "buying_signal"
    QUESTION = "question"
    FEATURE_INTEREST = "feature_interest"
    PERSONA = "persona"
    ROLE = "role"
    URGENCY = "urgency"
    UNANSWERED_QUESTION = "unanswered_question"
    DECISION_CRITERIA = "decision_criteria"
    NEXT_STEP = "next_step"


class CrmExportStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"
    DRY_RUN_COMPLETED = "dry_run_completed"


class ModelInvocationPurpose(StrEnum):
    REALTIME_HOST = "realtime_host"
    SCREEN_SUMMARY = "screen_summary"
    RECIPE_GENERATION = "recipe_generation"
    LEAD_SUMMARY = "lead_summary"
    EMBEDDING = "embedding"
    VISION_FALLBACK = "vision_fallback"
    SAFETY_CLASSIFICATION = "safety_classification"


class ArtifactKind(StrEnum):
    SCREENSHOT = "screenshot"
    RECORDING = "recording"
    BROWSER_TRACE = "browser_trace"
    GENERATED_REPORT = "generated_report"
    MODEL_DEBUG = "model_debug"
    TRANSCRIPT_EXPORT = "transcript_export"
    OTHER = "other"


class EventOutboxStatus(StrEnum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"


def check_values(enum_type: type[StrEnum]) -> str:
    return ", ".join(f"'{member.value}'" for member in enum_type)
