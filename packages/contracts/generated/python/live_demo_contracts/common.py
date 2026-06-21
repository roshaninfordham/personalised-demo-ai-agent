# Generated from packages/contracts/schemas. Do not edit manually.
# ruff: noqa: E501, F401, RUF100

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type UuidString = str


type IsoDateTimeString = str


type TraceId = str


type ProviderName = str


type JsonValue = str | float | int | bool | None | list[JsonValue] | dict[str, JsonValue]


type Metadata = dict[str, JsonValue]


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


class SessionStatus(StrEnum):
    CREATED = "created"
    PREWARMING = "prewarming"
    WAITING_FOR_USER = "waiting_for_user"
    LIVE = "live"
    ENDING = "ending"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    width: float
    height: float


type PaginationCursor = str


class ApiErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str
    trace_id: str
    details: Metadata


class ApiErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error: ApiErrorDetail


class ProductConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allowed_domains: list[str] = Field(default_factory=list)
    default_never_click: list[str] = Field(default_factory=list)
    demo_credentials_configured: bool | None = None
    preferred_recipe_id: UuidString | None = None
    browser_viewport: Metadata | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: UuidString
    product_name: str
    product_url: str
    default_persona: str | None = None
    product_summary: str | None = None
    confidence: float
    configuration: ProductConfiguration
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString


class CreateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str
    product_url: str
    default_persona: str | None = None
    product_summary: str | None = None
    configuration: ProductConfiguration | None = None


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str | None = None
    product_url: str | None = None
    default_persona: str | None = None
    product_summary: str | None = None
    configuration: ProductConfiguration | None = None


class ListProductsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProductResponse] = Field(default_factory=list)
    next_cursor: PaginationCursor | None


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


class ProductGuidanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guidance_id: UuidString
    product_id: UuidString
    guidance_type: ProductGuidanceType
    title: str | None = None
    content: Metadata
    source_uri: str | None = None
    created_at: IsoDateTimeString
    updated_at: IsoDateTimeString


class CreateProductGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guidance_type: ProductGuidanceType
    title: str | None = None
    content: Metadata
    source_uri: str | None = None


class UpdateProductGuidanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guidance_type: ProductGuidanceType | None = None
    title: str | None = None
    content: Metadata | None = None
    source_uri: str | None = None


class ListProductGuidanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ProductGuidanceResponse] = Field(default_factory=list)
    next_cursor: PaginationCursor | None
