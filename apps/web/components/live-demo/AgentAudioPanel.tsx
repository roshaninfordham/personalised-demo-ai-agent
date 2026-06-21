import type { CallConnectionStatus } from "../../lib/media/mediaTypes";
import { Badge } from "../ui/Badge";

export function AgentAudioPanel({ status }: { status: CallConnectionStatus }) {
  return (
    <div className="empty-state">
      <div className="row">
        <strong>Agent audio</strong>
        <Badge tone={status === "connected" ? "success" : "warning"}>{status}</Badge>
      </div>
      <p style={{ marginBottom: 0 }}>
        {status === "connected"
          ? "Realtime media transport is connected."
          : "Voice backend is not connected in this phase unless join config provides a real room."}
      </p>
    </div>
  );
}
