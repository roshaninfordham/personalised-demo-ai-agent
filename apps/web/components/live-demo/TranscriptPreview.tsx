import type { TranscriptItem } from "../../lib/events/eventTypes";

export function TranscriptPreview({ items }: { items: TranscriptItem[] }) {
  const latest = items.slice(-2);
  if (latest.length === 0) {
    return <p className="muted">Transcript preview will appear after transcript events arrive.</p>;
  }
  return (
    <div aria-live="polite" className="stack">
      {latest.map((item) => (
        <div key={item.transcriptEventId}>
          <strong>{item.speaker}</strong>
          <span className="muted"> {item.chunkType}</span>
          <div>{item.text}</div>
        </div>
      ))}
    </div>
  );
}
