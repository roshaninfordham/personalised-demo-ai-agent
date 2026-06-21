import type { EventConnectionStatus } from "../../lib/events/eventTypes";
import { Badge } from "../ui/Badge";

export function ConnectionStatus({ status }: { status: EventConnectionStatus }) {
  const tone = status === "connected" ? "success" : status === "failed" || status === "disconnected" ? "danger" : "warning";
  return (
    <span aria-live="polite">
      <Badge tone={tone}>Events: {status}</Badge>
    </span>
  );
}
