import type { DemoSessionStateResponse } from "@live-demo-agent/contracts";

import type { EventConnectionStatus } from "../../lib/events/eventTypes";
import { Badge } from "../ui/Badge";
import { ConnectionStatus } from "./ConnectionStatus";
import { EndDemoButton } from "./EndDemoButton";

export function SessionStatusBar({
  sessionId,
  sessionState,
  eventStatus,
}: {
  sessionId: string;
  sessionState: DemoSessionStateResponse | null;
  eventStatus: EventConnectionStatus;
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
          <ConnectionStatus status={eventStatus} />
          <EndDemoButton sessionId={sessionId} />
        </div>
      </div>
    </section>
  );
}
