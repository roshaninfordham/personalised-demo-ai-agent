import type { TranscriptEvent } from "@live-demo-agent/contracts";

const EMPTY_TRANSCRIPT: TranscriptEvent[] = [];

export function TranscriptPanel() {
  return (
    <section style={{ border: "1px solid #d4d4d8", borderRadius: 8, padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Transcript</h2>
      <p>{EMPTY_TRANSCRIPT.length} transcript events.</p>
    </section>
  );
}
