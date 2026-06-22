import type { BoundingBox, TranscriptChunkType, TranscriptSpeaker } from "@live-demo-agent/contracts";

import type { BrowserFrameState } from "../browser-view/frameStore";
import { getPublicConfig } from "../config/publicConfig";
import { eventLagMs, nowIso } from "../utils/time";
import type {
  ClickRippleState,
  ElementHighlightState,
  LearningMilestone,
  LiveDemoClientState,
  LiveDemoEvent,
  TranscriptItem,
} from "./eventTypes";

export function reduceEvent(
  state: LiveDemoClientState,
  event: LiveDemoEvent,
  receivedAtMs: number,
): LiveDemoClientState {
  if (state.processedEventIds.has(event.event_id)) return state;
  state.processedEventIds.add(event.event_id);
  state.recentEvents.push(event);
  state.latency.metrics.append("event_lag", eventLagMs(event.created_at, receivedAtMs));

  switch (event.event_type) {
    case "session.created":
      state.sessionStatus = "created";
      break;
    case "session.prewarming.started":
      state.sessionStatus = "prewarming";
      markMilestone(state, "loaded_product_url", "Loading product URL", event.created_at);
      break;
    case "session.prewarming.completed":
    case "session.waiting_for_user":
      state.sessionStatus = "waiting_for_user";
      markMilestone(state, "ready_to_present", "Ready to present", event.created_at);
      break;
    case "session.prewarming.degraded":
      state.sessionStatus = "waiting_for_user";
      state.errors.push({
        code: "prewarm_degraded",
        message: "Session is ready with degraded capabilities.",
        receivedAt: nowIso(),
      });
      break;
    case "session.prewarming.failed":
    case "session.failed":
      state.sessionStatus = "failed";
      state.errors.push({ code: "session_failed", message: "Session setup failed.", receivedAt: nowIso() });
      break;
    case "session.started":
    case "session.live.started":
      state.sessionStatus = "live";
      break;
    case "session.ended":
      state.sessionStatus = "completed";
      break;
    case "session.completed_with_warnings":
      state.sessionStatus = "completed";
      state.errors.push({
        code: "completed_with_warnings",
        message: "Session ended with cleanup warnings.",
        receivedAt: nowIso(),
      });
      break;
    case "session.recovery.started":
      state.sessionStatus = "recovery";
      state.errors.push({ code: "session_recovery", message: "Re-checking browser state.", receivedAt: nowIso() });
      break;
    case "session.recovery.resolved":
      state.sessionStatus = "live";
      break;
    case "session.ending":
      state.sessionStatus = "ending";
      break;
    case "browser.navigation.started":
      markMilestone(state, "loaded_product_url", "Loading product URL", event.created_at);
      break;
    case "browser.navigation.completed":
      markMilestone(state, "loaded_product_url", "Loaded product URL", event.created_at);
      break;
    case "browser.screen.updated":
      reduceScreenUpdated(state, event);
      break;
    case "browser.cursor.move":
      reduceCursorMove(state, event);
      break;
    case "browser.cursor.click":
    case "browser.cursor.ripple":
      reduceRipple(state, event);
      break;
    case "browser.element.highlight":
      reduceHighlight(state, event);
      break;
    case "browser.action.completed":
      appendLatency(state, "browser_action", numberPayload(event.payload.latency_ms));
      break;
    case "browser.action.failed":
      state.errors.push({ code: "browser_action_failed", message: "Browser action failed.", receivedAt: nowIso() });
      if (event.payload.policy_decision === "blocked" || event.payload.reason_code === "dangerous_action") {
        markMilestone(state, "blocked_risky_actions", "Blocked risky action", event.created_at);
      }
      break;
    case "browser.policy.blocked":
      markMilestone(state, "blocked_risky_actions", "Blocked risky action", event.created_at);
      break;
    case "transcript.partial":
      reduceTranscript(state, event, "partial");
      break;
    case "transcript.final":
      reduceTranscript(state, event, "final");
      break;
    case "agent.interrupted":
      markAssistantInterrupted(state);
      break;
    case "learner.demo_graph.updated":
      markMilestone(state, "built_demo_route", "Built demo route", event.created_at);
      break;
    case "learner.screen_summary.ready":
      markMilestone(state, "ready_to_present", "Ready to present", event.created_at);
      break;
    default:
      break;
  }

  state.version += 1;
  return state;
}

function reduceScreenUpdated(state: LiveDemoClientState, event: LiveDemoEvent): void {
  const payload = event.payload;
  const screenId = stringPayload(payload.screen_id) ?? "screen_unknown";
  const screenHash = stringPayload(payload.screen_hash) ?? screenId;
  const imageUrl =
    stringPayload(payload.image_url) ??
    stringPayload(payload.screenshot_url) ??
    stringPayload(payload.screenshot_uri) ??
    screenshotPayload(payload.screenshot) ??
    null;
  const frame: BrowserFrameState = {
    screenId,
    screenHash,
    imageUrl,
    width: numberPayload(payload.width) ?? 1440,
    height: numberPayload(payload.height) ?? 900,
    updatedAt: event.created_at,
    stale: Date.now() - Date.parse(event.created_at) > getPublicConfig().frameStaleAfterMs,
  };
  const title = stringPayload(payload.title);
  if (title !== undefined) frame.title = title;
  const url = stringPayload(payload.url);
  if (url !== undefined) frame.url = url;
  state.currentFrame = frame;
  const safeActions = numberPayload(payload.safe_action_count);
  if (safeActions !== undefined) {
    state.learning.safeActionCount = safeActions;
    if (safeActions > 0) {
      markMilestone(state, "found_clickable_actions", "Found clickable actions", event.created_at);
    }
  }
  const summary = stringPayload(payload.summary)?.toLowerCase() ?? "";
  if (/\b(dashboard|overview|metrics|analytics|reports)\b/.test(summary)) {
    markMilestone(state, "possible_detected_dashboard", "Possible dashboard detected", event.created_at);
  }
}

function reduceCursorMove(state: LiveDemoClientState, event: LiveDemoEvent): void {
  const x = numberPayload(event.payload.x) ?? 0;
  const y = numberPayload(event.payload.y) ?? 0;
  const nextCursor: Omit<LiveDemoClientState["cursor"], "controlPoint"> = {
    visible: true,
    source: state.cursor.target ?? { x, y },
    target: { x, y },
    startedAtMs: Date.now(),
    durationMs: numberPayload(event.payload.duration_ms) ?? 350,
    easing: event.payload.easing === "linear" ? "linear" : "easeOutCubic",
    lastUpdatedAt: event.created_at,
  };
  const controlPoint = pointPayload(event.payload.control_point);
  state.cursor = controlPoint === undefined ? nextCursor : { ...nextCursor, controlPoint };
}

function reduceRipple(state: LiveDemoClientState, event: LiveDemoEvent): void {
  const x = numberPayload(event.payload.x) ?? state.cursor.target?.x ?? 0;
  const y = numberPayload(event.payload.y) ?? state.cursor.target?.y ?? 0;
  const ripple: ClickRippleState = { id: event.event_id, x, y, startedAtMs: Date.now() };
  state.ripples.push(ripple);
}

function reduceHighlight(state: LiveDemoClientState, event: LiveDemoEvent): void {
  const elementId = stringPayload(event.payload.element_id);
  const bbox = bboxPayload(event.payload.bbox);
  if (elementId === undefined || bbox === undefined) return;
  const highlight: ElementHighlightState = {
    elementId,
    bbox,
    startedAtMs: Date.now(),
    durationMs: numberPayload(event.payload.duration_ms) ?? 1200,
  };
  const label = stringPayload(event.payload.label);
  if (label !== undefined) highlight.label = label;
  const riskLevel = riskLevelPayload(event.payload.risk_level);
  if (riskLevel !== undefined) highlight.riskLevel = riskLevel;
  state.highlights.set(elementId, highlight);
}

function reduceTranscript(
  state: LiveDemoClientState,
  event: LiveDemoEvent,
  defaultChunkType: TranscriptChunkType,
): void {
  const speaker = transcriptSpeaker(event.payload.speaker) ?? "assistant";
  const chunkType = transcriptChunk(event.payload.chunk_type) ?? defaultChunkType;
  const text = stringPayload(event.payload.text) ?? "";
  const turnId = stringPayload(event.payload.turn_id);
  const transcriptEventId = stringPayload(event.payload.transcript_event_id) ?? event.event_id;
  const item: TranscriptItem = {
    transcriptEventId,
    speaker,
    chunkType,
    text,
    createdAt: event.created_at,
  };
  if (turnId !== undefined) item.turnId = turnId;
  const confidence = numberPayload(event.payload.confidence);
  if (confidence !== undefined) item.confidence = confidence;
  const key = turnId === undefined ? undefined : `${speaker}:${turnId}`;
  const existingId = key === undefined ? undefined : state.transcript.partialByTurnKey.get(key);
  if (chunkType === "final" && key !== undefined && existingId !== undefined) {
    const existing = state.transcript.itemsById.get(existingId);
    if (existing !== undefined) {
      existing.text = text;
      existing.chunkType = "final";
      if (confidence === undefined) {
        delete existing.confidence;
      } else {
        existing.confidence = confidence;
      }
      state.transcript.itemsById.set(existingId, existing);
      state.transcript.partialByTurnKey.delete(key);
      return;
    }
  }
  state.transcript.items.push(item);
  state.transcript.itemsById.set(transcriptEventId, item);
  if (chunkType === "partial" && key !== undefined) {
    state.transcript.partialByTurnKey.set(key, transcriptEventId);
  }
}

function markAssistantInterrupted(state: LiveDemoClientState): void {
  const items = state.transcript.items.toArray();
  const latest = [...items].reverse().find((item) => item.speaker === "assistant" && item.chunkType === "partial");
  if (latest !== undefined) latest.chunkType = "interrupted";
}

function markMilestone(
  state: LiveDemoClientState,
  milestone: LearningMilestone,
  label: string,
  updatedAt: string,
): void {
  state.learning.milestones.set(milestone, { completed: true, label, updatedAt });
}

function appendLatency(state: LiveDemoClientState, name: "browser_action", value: number | undefined): void {
  if (value !== undefined) state.latency.metrics.append(name, value);
}

function stringPayload(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function screenshotPayload(value: unknown): string | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  const record = value as Record<string, unknown>;
  return stringPayload(record.presigned_url) ?? stringPayload(record.content_url);
}

function numberPayload(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function pointPayload(value: unknown): { x: number; y: number } | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  const record = value as Record<string, unknown>;
  const x = numberPayload(record.x);
  const y = numberPayload(record.y);
  return x === undefined || y === undefined ? undefined : { x, y };
}

function bboxPayload(value: unknown): BoundingBox | undefined {
  if (typeof value !== "object" || value === null) return undefined;
  const record = value as Record<string, unknown>;
  const x = numberPayload(record.x);
  const y = numberPayload(record.y);
  const width = numberPayload(record.width);
  const height = numberPayload(record.height);
  if (x === undefined || y === undefined || width === undefined || height === undefined) return undefined;
  return { x, y, width, height };
}

function riskLevelPayload(value: unknown): ElementHighlightState["riskLevel"] | undefined {
  if (value === "low" || value === "medium" || value === "high" || value === "blocked" || value === "unknown") {
    return value;
  }
  return undefined;
}

function transcriptSpeaker(value: unknown): TranscriptSpeaker | undefined {
  if (value === "user" || value === "assistant" || value === "system" || value === "tool") return value;
  return undefined;
}

function transcriptChunk(value: unknown): TranscriptChunkType | undefined {
  if (value === "partial" || value === "final" || value === "interrupted") return value;
  return undefined;
}
