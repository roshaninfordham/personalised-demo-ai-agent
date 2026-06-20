import { CursorOverlay } from "./CursorOverlay";

type BrowserViewportProps = {
  sessionId: string;
};

export function BrowserViewport({ sessionId }: BrowserViewportProps) {
  return (
    <section
      style={{
        aspectRatio: "16 / 9",
        border: "1px solid #d4d4d8",
        borderRadius: 8,
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div style={{ padding: 16 }}>
        <h2 style={{ marginTop: 0 }}>Browser Viewport</h2>
        <p>Browser streaming is not implemented in Phase 1.</p>
        <p>Session: {sessionId}</p>
      </div>
      <CursorOverlay x={64} y={64} />
    </section>
  );
}
