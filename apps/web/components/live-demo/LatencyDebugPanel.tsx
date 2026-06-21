import type { LatencyMetricName, LatencySummary } from "../../lib/metrics/latencyMetrics";
import { getPublicConfig } from "../../lib/config/publicConfig";
import type { LiveDemoClientState } from "../../lib/events/eventTypes";
import { Badge } from "../ui/Badge";

const labels: Array<[LatencyMetricName, string]> = [
  ["event_lag", "Event lag"],
  ["first_audio", "First audio"],
  ["turn", "Turn"],
  ["stt", "STT"],
  ["llm", "LLM"],
  ["tts", "TTS"],
  ["browser_action", "Browser action"],
  ["screen_read", "Screen read"],
];

export function LatencyDebugPanel({
  summaries,
  state,
}: {
  summaries: Record<LatencyMetricName, LatencySummary>;
  state: LiveDemoClientState;
}) {
  if (!getPublicConfig().enableDebugPanel) return null;
  return (
    <section className="card">
      <div className="card-body stack">
        <div className="panel-title">
          <h2>Latency debug</h2>
          <Badge>{state.connectionStatus}</Badge>
        </div>
        <div className="metric-grid">
          {labels.map(([name, label]) => (
            <div key={name} className="metric-card">
              <strong>{label}</strong>
              <div className="muted">
                latest {formatMs(summaries[name].latest)} · p50 {formatMs(summaries[name].p50)} · p95{" "}
                {formatMs(summaries[name].p95)}
              </div>
            </div>
          ))}
        </div>
        <div className="row">
          <Badge>invalid {String(state.latency.invalidEventCount)}</Badge>
          <Badge>reconnects {String(state.latency.reconnectCount)}</Badge>
          <Badge>dropped {String(state.latency.droppedEventCount)}</Badge>
        </div>
      </div>
    </section>
  );
}

function formatMs(value: number | null): string {
  return value === null ? "n/a" : `${String(Math.round(value))} ms`;
}
