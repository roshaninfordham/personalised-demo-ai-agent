import { describe, expect, it } from "vitest";

import { reduceEvent } from "../lib/events/eventReducer";
import { createInitialLiveDemoState } from "../lib/events/eventStore";
import type { LiveDemoEvent } from "../lib/events/eventTypes";

describe("eventReducer", () => {
  it("updates frame, milestones, and dedupes duplicate events", () => {
    const state = createInitialLiveDemoState("00000000-0000-0000-0000-000000000010");
    const event = eventOf("browser.screen.updated", {
      screen_id: "screen_a",
      screen_hash: "hash_a",
      image_url: "https://example.com/screen.webp",
      summary: "Dashboard metrics",
      safe_action_count: 4,
    });
    reduceEvent(state, event, Date.parse(event.created_at));
    reduceEvent(state, event, Date.parse(event.created_at));
    expect(state.currentFrame?.screenId).toBe("screen_a");
    expect(state.recentEvents.length).toBe(1);
    expect(state.learning.safeActionCount).toBe(4);
    expect(state.learning.milestones.get("possible_detected_dashboard")?.completed).toBe(true);
  });

  it("merges partial and final transcript deterministically", () => {
    const state = createInitialLiveDemoState("00000000-0000-0000-0000-000000000010");
    reduceEvent(
      state,
      eventOf("transcript.partial", { speaker: "assistant", chunk_type: "partial", text: "hel", turn_id: "t1" }),
      Date.now(),
    );
    reduceEvent(
      state,
      eventOf("transcript.final", { speaker: "assistant", chunk_type: "final", text: "hello", turn_id: "t1" }, "e2"),
      Date.now(),
    );
    const items = state.transcript.items.toArray();
    expect(items).toHaveLength(1);
    expect(items[0]?.text).toBe("hello");
    expect(items[0]?.chunkType).toBe("final");
  });
});

function eventOf(eventType: string, payload: Record<string, unknown>, eventId = "e1"): LiveDemoEvent {
  return {
    event_id: eventId,
    organization_id: "00000000-0000-0000-0000-000000000001",
    session_id: "00000000-0000-0000-0000-000000000010",
    trace_id: "trace_test",
    event_type: eventType,
    created_at: new Date("2026-06-20T12:00:00.000Z").toISOString(),
    payload,
  };
}
