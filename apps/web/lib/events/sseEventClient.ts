import { getPublicConfig } from "../config/publicConfig";
import { demoSessionEventsEndpoint } from "../api/endpoints";
import type { EventConnectionStatus, LiveDemoEvent } from "./eventTypes";
import type { LiveEventClient } from "./eventClient";

const NAMED_EVENT_TYPES = [
  "session.created",
  "session.prewarming.started",
  "session.prewarming.completed",
  "session.prewarming.degraded",
  "session.prewarming.failed",
  "session.waiting_for_user",
  "session.started",
  "session.live.started",
  "session.ending",
  "session.ended",
  "session.failed",
  "browser.navigation.started",
  "browser.navigation.completed",
  "browser.screen.updated",
  "browser.cursor.move",
  "browser.cursor.click",
  "browser.cursor.ripple",
  "browser.element.highlight",
  "browser.action.completed",
  "browser.action.failed",
  "browser.policy.blocked",
  "transcript.partial",
  "transcript.final",
  "agent.interrupted",
  "learner.demo_graph.updated",
  "learner.screen_summary.ready",
  "lead_summary.ready",
] as const;

export class SseEventClient implements LiveEventClient {
  private source: EventSource | null = null;
  private status: EventConnectionStatus = "idle";
  private sessionId: string | null = null;
  private reconnectAttempts = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private readonly listeners = new Set<(event: LiveDemoEvent) => void>();
  private readonly statusListeners = new Set<(status: EventConnectionStatus) => void>();

  connect(sessionId: string): void {
    if (this.source !== null && this.sessionId === sessionId) return;
    this.disconnect();
    this.sessionId = sessionId;
    this.setStatus("connecting");
    this.open();
  }

  disconnect(): void {
    if (this.reconnectTimer !== null) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.source?.close();
    this.source = null;
    this.setStatus("disconnected");
  }

  subscribe(listener: (event: LiveDemoEvent) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  subscribeStatus(listener: (status: EventConnectionStatus) => void): () => void {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }

  getStatus(): EventConnectionStatus {
    return this.status;
  }

  private open(): void {
    if (this.sessionId === null || typeof EventSource === "undefined") {
      this.setStatus("failed");
      return;
    }
    const config = getPublicConfig();
    const endpoint = demoSessionEventsEndpoint(this.sessionId);
    this.source = new EventSource(`${config.eventsBaseUrl}${endpoint}`);
    this.source.onopen = () => {
      this.reconnectAttempts = 0;
      this.setStatus("connected");
    };
    const handleMessage = (message: MessageEvent<string>) => {
      const event = parseLiveEvent(message.data);
      if (event === null) return;
      for (const listener of this.listeners) listener(event);
    };
    this.source.onmessage = handleMessage;
    for (const eventType of NAMED_EVENT_TYPES) {
      this.source.addEventListener(eventType, handleMessage as EventListener);
    }
    this.source.addEventListener("heartbeat", () => {
      this.reconnectAttempts = 0;
      this.setStatus("connected");
    });
    this.source.onerror = () => {
      this.source?.close();
      this.source = null;
      this.setStatus("reconnecting");
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.sessionId === null) return;
    const delay = reconnectDelayMs(this.reconnectAttempts);
    this.reconnectAttempts += 1;
    this.reconnectTimer = setTimeout(() => {
      this.open();
    }, delay);
  }

  private setStatus(status: EventConnectionStatus): void {
    this.status = status;
    for (const listener of this.statusListeners) listener(status);
  }
}

export function parseLiveEvent(value: string): LiveDemoEvent | null {
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!isLiveDemoEvent(parsed)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function reconnectDelayMs(attempt: number, seed = 1): number {
  const base = 500;
  const max = 5000;
  const delay = Math.min(max, base * 2 ** attempt);
  const pseudo = ((seed * 1103515245 + attempt * 12345) >>> 0) / 2 ** 32;
  return Math.round(delay * (0.8 + pseudo * 0.4));
}

function isLiveDemoEvent(value: unknown): value is LiveDemoEvent {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.event_id === "string" &&
    (typeof record.session_id === "string" || record.session_id === null) &&
    (typeof record.organization_id === "string" || record.organization_id === null) &&
    typeof record.event_type === "string" &&
    typeof record.created_at === "string" &&
    typeof record.trace_id === "string" &&
    typeof record.payload === "object" &&
    record.payload !== null &&
    !Array.isArray(record.payload)
  );
}
