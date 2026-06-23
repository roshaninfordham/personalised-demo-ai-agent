import type { DemoSessionStateResponse } from "@live-demo-agent/contracts";

import type { EventConnectionStatus } from "../../lib/events/eventTypes";
import { Badge } from "../ui/Badge";
import { ConnectionStatus } from "./ConnectionStatus";
import { EndDemoButton } from "./EndDemoButton";

export function SessionStatusBar({
  sessionId,
  sessionState,
  eventStatus,
  agentPhase,
}: {
  sessionId: string;
  sessionState: DemoSessionStateResponse | null;
  eventStatus: EventConnectionStatus;
  agentPhase: string | null;
}) {
  const status = sessionState?.session.status ?? "loading";
  const productName = sessionState?.session.product_name ?? "Product session";
  return (
    <section className="card">
      <div className="card-body session-bar">
        <div>
          <strong>{productName}</strong>
          <div className="muted">Session {sessionId}</div>
        </div>
        <div className="row">
          <Badge tone={status === "completed" ? "success" : status === "failed" ? "danger" : "warning"}>
            {status}
          </Badge>
          {agentPhase === null ? null : <Badge>{formatPhase(agentPhase)}</Badge>}
          <ConnectionStatus status={eventStatus} />
          <EndDemoButton sessionId={sessionId} />
        </div>
      </div>
    </section>
  );
}

function formatPhase(value: string): string {
  return value.toLowerCase().replaceAll("_", " ");
}
