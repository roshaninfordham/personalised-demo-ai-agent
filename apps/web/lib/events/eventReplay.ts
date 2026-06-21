import type { LiveDemoEvent } from "./eventTypes";

export function createMockEventReplay(sessionId: string): LiveDemoEvent[] {
  const base = Date.now();
  const event = (index: number, eventType: string, payload: Record<string, unknown>): LiveDemoEvent => ({
    event_id: `00000000-0000-0000-0000-${String(index).padStart(12, "0")}`,
    session_id: sessionId,
    organization_id: "00000000-0000-0000-0000-000000000001",
    event_type: eventType,
    created_at: new Date(base + index * 400).toISOString(),
    trace_id: `mock-${String(index)}`,
    payload,
  });
  return [
    event(1, "session.prewarming.started", {}),
    event(2, "browser.navigation.completed", { url: "https://example.com" }),
    event(3, "browser.screen.updated", {
      screen_id: "screen_mock_dashboard",
      screen_hash: "mock_hash",
      title: "Dashboard",
      url: "https://example.com/dashboard",
      summary: "Dashboard with metrics, reports, and analytics cards.",
      safe_action_count: 4,
      image_url: null,
      width: 1440,
      height: 900,
    }),
    event(4, "browser.cursor.move", { x: 480, y: 240, duration_ms: 480 }),
    event(5, "browser.element.highlight", {
      element_id: "el_button_reports",
      label: "Reports",
      bbox: { x: 420, y: 210, width: 140, height: 42 },
      duration_ms: 1600,
      risk_level: "low",
    }),
    event(6, "browser.cursor.click", { x: 490, y: 231 }),
    event(7, "browser.action.completed", { latency_ms: 180 }),
    event(8, "transcript.partial", {
      transcript_event_id: "00000000-0000-0000-0000-000000000101",
      speaker: "assistant",
      chunk_type: "partial",
      text: "Here is the metrics dashboard",
      turn_id: "turn_1",
    }),
    event(9, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000102",
      speaker: "assistant",
      chunk_type: "final",
      text: "Here is the metrics dashboard with the core reports surfaced.",
      turn_id: "turn_1",
    }),
    event(10, "learner.screen_summary.ready", {}),
    event(11, "learner.demo_graph.updated", {}),
    event(12, "lead_summary.ready", {}),
  ];
}
