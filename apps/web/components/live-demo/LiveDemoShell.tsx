"use client";

import { useBrowserFrame } from "../../hooks/useBrowserFrame";
import { useCursorOverlay } from "../../hooks/useCursorOverlay";
import { useDemoSession } from "../../hooks/useDemoSession";
import { useLatencyMetrics } from "../../hooks/useLatencyMetrics";
import { useSessionEvents } from "../../hooks/useSessionEvents";
import { useTranscript } from "../../hooks/useTranscript";
import { getPublicConfig } from "../../lib/config/publicConfig";
import { BrowserViewport } from "./BrowserViewport";
import { CallPanel } from "./CallPanel";
import { ErrorBanner } from "./ErrorBanner";
import { LatencyDebugPanel } from "./LatencyDebugPanel";
import { LearningSidebar } from "./LearningSidebar";
import { SessionStatusBar } from "./SessionStatusBar";
import { TranscriptPanel } from "./TranscriptPanel";

export function LiveDemoShell({ sessionId }: { sessionId: string }) {
  const sessionLoadState = useDemoSession(sessionId);
  const { state } = useSessionEvents(sessionId);
  const frame = useBrowserFrame(state);
  const transcript = useTranscript(state);
  const latency = useLatencyMetrics(state);
  const { cursor, highlights } = useCursorOverlay(state);
  const config = getPublicConfig();
  const sessionState = sessionLoadState.status === "loaded" ? sessionLoadState.data : null;

  return (
    <div className="live-shell">
      <div className="live-main">
        <SessionStatusBar sessionId={sessionId} sessionState={sessionState} eventStatus={state.connectionStatus} />
        {config.enableMockEvents ? <ErrorBanner message="Mock events enabled. This is not a live backend stream." /> : null}
        {sessionLoadState.status === "failed" ? <ErrorBanner message={sessionLoadState.message} /> : null}
        <BrowserViewport
          frame={frame}
          cursor={cursor}
          highlights={highlights}
          ripples={state.ripples.toArray()}
          scrollIndicators={state.scrollIndicators.toArray()}
          connectionStatus={state.connectionStatus}
        />
        <CallPanel sessionId={sessionId} transcript={transcript} />
      </div>
      <aside className="live-side">
        <LearningSidebar learning={state.learning} recentEvents={state.recentEvents.toArray()} />
        <TranscriptPanel items={transcript} debug={config.enableDebugPanel} />
        <LatencyDebugPanel summaries={latency} state={state} />
      </aside>
    </div>
  );
}
