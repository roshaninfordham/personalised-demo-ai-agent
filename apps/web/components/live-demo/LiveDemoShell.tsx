"use client";

import { useCallback, useEffect, useState } from "react";
import type { DemoSessionStateResponse } from "@live-demo-agent/contracts";

import { getDemoSessionState, type TextTurnResponse } from "../../lib/api/demoSessionsApi";
import { useBrowserFrame } from "../../hooks/useBrowserFrame";
import { useCursorOverlay } from "../../hooks/useCursorOverlay";
import { useDemoSession } from "../../hooks/useDemoSession";
import { useLatencyMetrics } from "../../hooks/useLatencyMetrics";
import { useSessionEvents } from "../../hooks/useSessionEvents";
import { useTranscript } from "../../hooks/useTranscript";
import { getPublicConfig } from "../../lib/config/publicConfig";
import type { LiveDemoEvent } from "../../lib/events/eventTypes";
import { Tabs } from "../ui/Tabs";
import { BrowserViewport } from "./BrowserViewport";
import { CallPanel } from "./CallPanel";
import { ErrorBanner } from "./ErrorBanner";
import { LatencyDebugPanel } from "./LatencyDebugPanel";
import { LearningSidebar } from "./LearningSidebar";
import { SessionStatusBar } from "./SessionStatusBar";
import { TranscriptPanel } from "./TranscriptPanel";

export function LiveDemoShell({ sessionId }: { sessionId: string }) {
  const sessionLoadState = useDemoSession(sessionId);
  const { state, store } = useSessionEvents(sessionId);
  const frame = useBrowserFrame(state);
  const transcript = useTranscript(state);
  const latency = useLatencyMetrics(state);
  const { cursor, highlights } = useCursorOverlay(state);
  const config = getPublicConfig();
  const sessionState = sessionLoadState.status === "loaded" ? sessionLoadState.data : null;
  const [sidePanelOpen, setSidePanelOpen] = useState(true);
  const [fallbackPolling, setFallbackPolling] = useState(false);
  const dispatch = useCallback(
    (event: LiveDemoEvent, receivedAtMs?: number) => {
      store.dispatch(event, receivedAtMs);
    },
    [store],
  );

  useEffect(() => {
    if (sessionState === null) return;
    hydrateFromSessionState(dispatch, sessionId, sessionState);
  }, [dispatch, sessionId, sessionState]);

  useEffect(() => {
    const shouldPoll = state.connectionStatus !== "connected" || state.currentFrame === null;
    setFallbackPolling(shouldPoll);
    if (!shouldPoll) return undefined;
    let cancelled = false;
    const poll = async (): Promise<void> => {
      try {
        const next = await getDemoSessionState(sessionId);
        if (!cancelled) hydrateFromSessionState(dispatch, sessionId, next);
      } catch {
        // The SSE client owns connection errors. Polling is a best-effort fallback.
      }
    };
    void poll();
    const timer = window.setInterval(() => {
      void poll();
    }, 2000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [dispatch, sessionId, state.connectionStatus, state.currentFrame]);

  return (
    <div className="live-shell">
      <div className="live-main">
        <SessionStatusBar sessionId={sessionId} sessionState={sessionState} eventStatus={state.connectionStatus} />
        {config.enableMockEvents ? <ErrorBanner message="Mock events enabled. This is not a live backend stream." /> : null}
        {fallbackPolling && state.currentFrame !== null ? (
          <ErrorBanner message="Live events are reconnecting, so the room is using session-state polling." />
        ) : null}
        {sessionLoadState.status === "failed" ? <ErrorBanner message={sessionLoadState.message} /> : null}
        <BrowserViewport
          frame={frame}
          cursor={cursor}
          highlights={highlights}
          ripples={state.ripples.toArray()}
          scrollIndicators={state.scrollIndicators.toArray()}
          connectionStatus={state.connectionStatus}
        />
        <CallPanel
          sessionId={sessionId}
          transcript={transcript}
          eventStatus={state.connectionStatus}
          onFallbackTextTurn={(text, response) => {
            dispatchTextTurnFallback(dispatch, sessionId, text, response);
          }}
        />
      </div>
      <aside className={sidePanelOpen ? "live-side" : "live-side live-side-collapsed"}>
        <button
          type="button"
          className="button button-secondary side-toggle"
          onClick={() => {
            setSidePanelOpen((open) => !open);
          }}
        >
          {sidePanelOpen ? "Hide panel" : "Show panel"}
        </button>
        {sidePanelOpen ? (
          <Tabs
            initialTabId="assistant"
            tabs={[
              {
                id: "assistant",
                label: "Assistant",
                content: <TranscriptPanel items={transcript} debug={false} />,
              },
              {
                id: "learning",
                label: "Learning",
                content: <LearningSidebar learning={state.learning} recentEvents={state.recentEvents.toArray()} />,
              },
              {
                id: "debug",
                label: "Debug",
                content: <LatencyDebugPanel summaries={latency} state={state} />,
              },
            ]}
          />
        ) : null}
      </aside>
    </div>
  );
}

function dispatchTextTurnFallback(
  dispatch: (event: LiveDemoEvent, receivedAtMs?: number) => void,
  sessionId: string,
  text: string,
  response: TextTurnResponse,
): void {
  const createdAt = new Date().toISOString();
  const base = {
    organization_id: null,
    session_id: sessionId,
    created_at: createdAt,
    trace_id: "frontend-text-fallback",
  };
  dispatch({
    ...base,
    event_id: `local-user:${response.turn_id}`,
    event_type: "transcript.final",
    payload: {
      transcript_event_id: `local-user:${response.turn_id}`,
      speaker: "user",
      chunk_type: "final",
      text,
      turn_id: response.turn_id,
    },
  });
  dispatch({
    ...base,
    event_id: `local-assistant:${response.turn_id}`,
    event_type: "transcript.final",
    payload: {
      transcript_event_id: `local-assistant:${response.turn_id}`,
      speaker: "assistant",
      chunk_type: "final",
      text: response.assistant_response,
      turn_id: response.turn_id,
    },
  });
  if (response.policy_blocked) {
    dispatch({
      ...base,
      event_id: `local-blocked:${response.turn_id}`,
      event_type: "browser.action.failed",
      payload: {
        policy_decision: "blocked",
        reason_code: "dangerous_action",
        label: response.action_taken ?? "Dangerous action",
        success: false,
      },
    });
    return;
  }
  if (response.action_taken !== null) {
    const bbox = fallbackActionBox(response.action_taken);
    const x = bbox.x + bbox.width / 2;
    const y = bbox.y + bbox.height / 2;
    dispatch({
      ...base,
      event_id: `local-cursor:${response.turn_id}`,
      event_type: "browser.cursor.move",
      payload: { x, y, duration_ms: 320 },
    });
    dispatch({
      ...base,
      event_id: `local-highlight:${response.turn_id}`,
      event_type: "browser.element.highlight",
      payload: {
        element_id: `local-action:${response.turn_id}`,
        label: response.action_taken,
        bbox,
        risk_level: "low",
        duration_ms: 2200,
      },
    });
    dispatch({
      ...base,
      event_id: `local-click:${response.turn_id}`,
      event_type: "browser.cursor.click",
      payload: { x, y },
    });
  }
}

function fallbackActionBox(label: string): { x: number; y: number; width: number; height: number } {
  const lower = label.toLowerCase();
  if (lower.includes("metric")) return { x: 550, y: 462, width: 340, height: 176 };
  if (lower.includes("report")) return { x: 1004, y: 462, width: 340, height: 176 };
  return { x: 96, y: 462, width: 340, height: 176 };
}

function hydrateFromSessionState(
  dispatch: (event: LiveDemoEvent, receivedAtMs?: number) => void,
  sessionId: string,
  sessionState: DemoSessionStateResponse,
): void {
  const screen = sessionState.live_state.current_screen;
  if (screen === null || typeof screen !== "object" || Array.isArray(screen)) return;
  const payload = screen as Record<string, unknown>;
  const screenId = typeof payload.screen_id === "string" ? payload.screen_id : "screen_snapshot";
  const screenHash = typeof payload.screen_hash === "string" ? payload.screen_hash : screenId;
  const createdAt = new Date().toISOString();
  dispatch(
    {
      event_id: `snapshot:${sessionId}:${screenId}:${screenHash}`,
      organization_id: null,
      session_id: sessionId,
      event_type: "browser.screen.updated",
      payload: {
        ...payload,
        safe_action_count: sessionState.live_state.safe_actions.length,
      },
      created_at: createdAt,
      trace_id: "frontend-snapshot",
    },
    Date.now(),
  );
}
