import type { EventEnvelope } from "@live-demo-agent/contracts";

const EMPTY_EVENTS: EventEnvelope[] = [];

export function EventSidebar() {
  return (
    <section style={{ border: "1px solid #d4d4d8", borderRadius: 8, padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Events</h2>
      <p>{EMPTY_EVENTS.length} events received.</p>
    </section>
  );
}
