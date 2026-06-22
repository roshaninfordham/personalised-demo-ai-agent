import type {
  BoundingBox,
  EventEnvelope,
  RiskLevel,
  TranscriptChunkType,
  TranscriptSpeaker,
} from "@live-demo-agent/contracts";

import type { BrowserFrameState } from "../browser-view/frameStore";
import type { Point } from "../browser-view/viewportMath";
import type { LatencyMetricName } from "../metrics/latencyMetrics";
import type { RingBuffer } from "../metrics/ringBuffer";
import type { LatencyMetrics } from "../metrics/latencyMetrics";

export type EventConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "failed";

export type LiveDemoEvent = Omit<EventEnvelope, "event_type" | "payload"> & {
  event_type: string;
  payload: Record<string, unknown>;
};

export type CursorState = {
  visible: boolean;
  source: Point | null;
  target: Point | null;
  controlPoint?: Point;
  startedAtMs: number;
  durationMs: number;
  easing: "easeOutCubic" | "linear";
  lastUpdatedAt: string;
};

export type ElementHighlightState = {
  elementId: string;
  bbox: BoundingBox;
  label?: string;
  riskLevel?: RiskLevel;
  startedAtMs: number;
  durationMs: number;
};

export type ClickRippleState = {
  id: string;
  x: number;
  y: number;
  startedAtMs: number;
};

export type ScrollIndicatorState = {
  id: string;
  direction: "up" | "down" | "left" | "right";
  startedAtMs: number;
};

export type TranscriptItem = {
  transcriptEventId: string;
  speaker: TranscriptSpeaker;
  chunkType: TranscriptChunkType;
  text: string;
  createdAt: string;
  startMs?: number;
  endMs?: number;
  confidence?: number;
  turnId?: string;
};

export type AuthScreenState = {
  loginRequired: boolean;
  confidence: number;
  detectedFields: string[];
  detectedActions: string[];
  safeOptions: string[];
  reasonCodes: string[];
};

export type TranscriptState = {
  items: RingBuffer<TranscriptItem>;
  itemsById: Map<string, TranscriptItem>;
  partialByTurnKey: Map<string, string>;
};

export type LearningMilestone =
  | "loaded_product_url"
  | "possible_detected_dashboard"
  | "detected_dashboard"
  | "found_clickable_actions"
  | "built_demo_route"
  | "blocked_risky_actions"
  | "ready_to_present";

export type LearningState = {
  milestones: Map<LearningMilestone, { completed: boolean; label: string; updatedAt?: string }>;
  safeActionCount: number;
};

export type ClientEventError = {
  code: string;
  message: string;
  receivedAt: string;
};

export type LatencyState = {
  metrics: LatencyMetrics;
  invalidEventCount: number;
  reconnectCount: number;
  droppedEventCount: number;
};

export type LiveDemoClientState = {
  sessionId: string;
  connectionStatus: EventConnectionStatus;
  sessionStatus: string | null;
  currentFrame: BrowserFrameState | null;
  authState: AuthScreenState | null;
  cursor: CursorState;
  highlights: Map<string, ElementHighlightState>;
  ripples: RingBuffer<ClickRippleState>;
  scrollIndicators: RingBuffer<ScrollIndicatorState>;
  transcript: TranscriptState;
  learning: LearningState;
  latency: LatencyState;
  recentEvents: RingBuffer<LiveDemoEvent>;
  processedEventIds: Set<string>;
  errors: RingBuffer<ClientEventError>;
  version: number;
};

export type EventMetricPayload = {
  metric: LatencyMetricName;
  latency_ms: number;
};
