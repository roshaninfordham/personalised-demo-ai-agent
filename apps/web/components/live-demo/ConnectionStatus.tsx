import type { EventConnectionStatus } from "../../lib/events/eventTypes";
import { Badge } from "../ui/Badge";

export function ConnectionStatus({ status }: { status: EventConnectionStatus }) {
  const tone = status === "connected" ? "success" : status === "failed" || status === "disconnected" ? "danger" : "warning";
  const label =
    status === "connected"
      ? "Live updates connected"
      : status === "connecting"
        ? "Connecting live updates"
        : "Using polling fallback";
  return (
    <span aria-live="polite">
      <Badge tone={tone}>{label}</Badge>
    </span>
  );
}
