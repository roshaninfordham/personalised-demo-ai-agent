import { LatencyMetrics } from "../metrics/latencyMetrics";
import { RingBuffer } from "../metrics/ringBuffer";
import { nowIso } from "../utils/time";
import { reduceEvent } from "./eventReducer";
import type {
  EventConnectionStatus,
  LearningMilestone,
  LiveDemoClientState,
  LiveDemoEvent,
  TranscriptState,
} from "./eventTypes";

export type LiveDemoStore = {
  getSnapshot(): LiveDemoClientState;
  subscribe(listener: () => void): () => void;
  dispatch(event: LiveDemoEvent, receivedAtMs?: number): void;
  setConnectionStatus(status: EventConnectionStatus): void;
  recordInvalidEvent(message: string): void;
};

export function createInitialLiveDemoState(sessionId: string): LiveDemoClientState {
  const transcript: TranscriptState = {
    items: new RingBuffer(500),
    itemsById: new Map(),
    partialByTurnKey: new Map(),
  };
  return {
    sessionId,
    connectionStatus: "idle",
    sessionStatus: null,
    agentPhase: null,
    currentFrame: null,
    authState: null,
    cursor: {
      visible: false,
      source: null,
      target: null,
      startedAtMs: 0,
      durationMs: 0,
      easing: "easeOutCubic",
      lastUpdatedAt: nowIso(),
    },
    highlights: new Map(),
    ripples: new RingBuffer(20),
    scrollIndicators: new RingBuffer(10),
    transcript,
    learning: { milestones: createMilestones(), safeActionCount: 0 },
    latency: {
      metrics: new LatencyMetrics(512),
      invalidEventCount: 0,
      reconnectCount: 0,
      droppedEventCount: 0,
    },
    recentEvents: new RingBuffer(1000),
    processedEventIds: new Set(),
    errors: new RingBuffer(100),
    version: 0,
  };
}

export function createLiveDemoStore(sessionId: string): LiveDemoStore {
  let state = createInitialLiveDemoState(sessionId);
  const listeners = new Set<() => void>();
  const notify = (): void => {
    state = { ...state, version: state.version + 1 };
    for (const listener of listeners) listener();
  };
  return {
    getSnapshot: () => state,
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    dispatch(event, receivedAtMs = Date.now()) {
      state = reduceEvent(state, event, receivedAtMs);
      notify();
    },
    setConnectionStatus(status) {
      if (status === "reconnecting") state.latency.reconnectCount += 1;
      state.connectionStatus = status;
      notify();
    },
    recordInvalidEvent(message) {
      state.latency.invalidEventCount += 1;
      state.errors.push({ code: "invalid_event", message, receivedAt: nowIso() });
      notify();
    },
  };
}

function createMilestones(): Map<LearningMilestone, { completed: boolean; label: string; updatedAt?: string }> {
  return new Map([
    ["loaded_product_url", { completed: false, label: "Loaded product URL" }],
    ["possible_detected_dashboard", { completed: false, label: "Possible dashboard detected" }],
    ["detected_dashboard", { completed: false, label: "Detected dashboard" }],
    ["found_clickable_actions", { completed: false, label: "Found clickable actions" }],
    ["built_demo_route", { completed: false, label: "Built demo route" }],
    ["blocked_risky_actions", { completed: false, label: "Blocked risky actions" }],
    ["ready_to_present", { completed: false, label: "Ready to present" }],
  ]);
}

let browserStore: LiveDemoStore | null = null;

export function getOrCreateLiveDemoStore(sessionId: string): LiveDemoStore {
  if (browserStore === null || browserStore.getSnapshot().sessionId !== sessionId) {
    browserStore = createLiveDemoStore(sessionId);
  }
  return browserStore;
}
