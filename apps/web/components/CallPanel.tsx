type CallPanelProps = {
  sessionId: string;
  status: string;
};

export function CallPanel({ sessionId, status }: CallPanelProps) {
  return (
    <section style={{ border: "1px solid #d4d4d8", borderRadius: 8, padding: 16 }}>
      <h2 style={{ marginTop: 0 }}>Call Panel</h2>
      <p>Session: {sessionId}</p>
      <p>Status: {status}</p>
      <p>Realtime media is not implemented in Phase 1.</p>
    </section>
  );
}
