import { BrowserViewport } from "../../../components/BrowserViewport";
import { CallPanel } from "../../../components/CallPanel";
import { EventSidebar } from "../../../components/EventSidebar";
import { LatencyDebugPanel } from "../../../components/LatencyDebugPanel";
import { TranscriptPanel } from "../../../components/TranscriptPanel";
import { createInitialSessionState } from "../../../lib/sessionStore";

type DemoPageProps = {
  params: Promise<{
    sessionId: string;
  }>;
};

export default async function DemoPage({ params }: DemoPageProps) {
  const { sessionId } = await params;
  const session = createInitialSessionState(sessionId);

  return (
    <main
      style={{
        display: "grid",
        gap: 16,
        gridTemplateColumns: "minmax(0, 1fr) 320px",
        minHeight: "100vh",
        padding: 16,
      }}
    >
      <section style={{ display: "grid", gap: 16 }}>
        <CallPanel sessionId={session.session_id} status={session.status} />
        <BrowserViewport sessionId={session.session_id} />
        <LatencyDebugPanel />
      </section>
      <aside style={{ display: "grid", gap: 16 }}>
        <EventSidebar />
        <TranscriptPanel />
      </aside>
    </main>
  );
}
