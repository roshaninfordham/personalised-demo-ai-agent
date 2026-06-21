"""Structured realtime agent decision model."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ToolName = Literal[
    "read_current_screen",
    "highlight_element",
    "click_element",
    "type_demo_text",
    "scroll",
    "go_back",
    "search_product_knowledge",
    "save_lead_insight",
]

MemoryType = Literal[
    "persona",
    "pain_point",
    "use_case",
    "objection",
    "buying_signal",
    "feature_interest",
    "question",
    "urgency",
    "preference",
    "unanswered_question",
]


class BrowserActionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action_id: str = Field(min_length=1, max_length=200)
    tool_name: ToolName
    reason: str = Field(min_length=1, max_length=500)
    arguments: dict[str, object] = Field(default_factory=dict)


class MemoryEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript_event_ids: list[str] = Field(default_factory=list, max_length=10)
    screen_ids: list[str] = Field(default_factory=list, max_length=10)
    action_ids: list[str] = Field(default_factory=list, max_length=10)

    def has_any(self) -> bool:
        return bool(self.transcript_event_ids or self.screen_ids or self.action_ids)


class MemoryUpdateDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: MemoryType
    content: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: MemoryEvidence


class AgentDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spoken_response: str = Field(min_length=0, max_length=500)
    browser_action: BrowserActionDecision | None
    memory_updates: list[MemoryUpdateDecision] = Field(max_length=5)
    confidence: float = Field(ge=0.0, le=1.0)
