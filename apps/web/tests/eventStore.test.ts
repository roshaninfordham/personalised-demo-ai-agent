import { describe, expect, it } from "vitest";

import { createLiveDemoStore } from "../lib/events/eventStore";
import { parseLiveEvent, reconnectDelayMs } from "../lib/events/sseEventClient";

describe("event store and SSE parsing", () => {
  it("records invalid events safely", () => {
    const store = createLiveDemoStore("00000000-0000-0000-0000-000000000010");
    store.recordInvalidEvent("bad event");
    expect(store.getSnapshot().latency.invalidEventCount).toBe(1);
    expect(store.getSnapshot().errors.length).toBe(1);
  });

  it("parses valid events and ignores invalid payloads", () => {
    const valid = JSON.stringify({
      event_id: "e1",
      organization_id: "00000000-0000-0000-0000-000000000001",
      session_id: "00000000-0000-0000-0000-000000000010",
      trace_id: "trace",
      event_type: "session.created",
      created_at: "2026-06-20T12:00:00.000Z",
      payload: {},
    });
    expect(parseLiveEvent(valid)?.event_type).toBe("session.created");
    expect(parseLiveEvent("{")).toBeNull();
  });

  it("uses deterministic bounded reconnect delay", () => {
    expect(reconnectDelayMs(0, 1)).toBe(reconnectDelayMs(0, 1));
    expect(reconnectDelayMs(20, 1)).toBeLessThanOrEqual(6000);
  });
});
