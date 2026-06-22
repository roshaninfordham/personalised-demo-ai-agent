"use client";

import { useEffect, useState } from "react";

import { getMetricsSummary, type MetricsSummary } from "../../lib/api/metricsApi";
import { Card, CardBody } from "../ui/Card";

type LoadState =
  | { status: "loading" }
  | { status: "loaded"; data: MetricsSummary }
  | { status: "failed"; message: string };

export function LocalMetricsPanel({ compact = false }: { compact?: boolean }) {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    getMetricsSummary()
      .then((data) => {
        if (active) setState({ status: "loaded", data });
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "failed",
            message: error instanceof Error ? error.message : "Metrics summary is unavailable.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const metrics = state.status === "loaded" ? metricRows(state.data) : [];
  return (
    <Card>
      <CardBody className="stack">
        <div className="panel-title">
          <h2>{compact ? "Local metrics" : "Local Metrics"}</h2>
          <span className="badge badge-warning">observability optional</span>
        </div>
        {state.status === "loading" ? <p className="muted">Loading local metrics...</p> : null}
        {state.status === "failed" ? (
          <div className="empty-state">
            <strong>Metrics summary unavailable</strong>
            <p className="muted">{state.message}</p>
          </div>
        ) : null}
        {state.status === "loaded" ? (
          <div className="metric-grid">
            {metrics.map(([label, value, detail]) => (
              <div className="metric-card" key={label}>
                <strong>{label}</strong>
                <span className="metric-value">{value}</span>
                <p className="muted">{detail}</p>
              </div>
            ))}
          </div>
        ) : null}
        <p className="muted">
          If Grafana is not running, start it with <code>make up-observability</code>.
        </p>
      </CardBody>
    </Card>
  );
}

function metricRows(data: MetricsSummary): Array<[string, string, string]> {
  return [
    ["Active sessions", String(data.active_sessions), "live/prewarming sessions right now"],
    ["Sessions today", String(data.sessions_today), "created in the local database today"],
    ["Browser actions", String(data.browser_actions_today), "safe and blocked browser actions today"],
    ["Policy blocks", String(data.policy_blocks_today), "blocked unsafe requests today"],
    [
      "Browser action latency",
      data.average_browser_action_ms === null
        ? "n/a"
        : `${String(Math.round(data.average_browser_action_ms))} ms`,
      "average local action latency from persisted events",
    ],
    [
      "Event lag",
      data.event_lag_ms === null ? "n/a" : `${String(Math.round(data.event_lag_ms))} ms`,
      "available from live debug/observability when enabled",
    ],
  ];
}
