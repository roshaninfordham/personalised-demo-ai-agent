import { getJoinConfig } from "../api/demoSessionsApi";
import type { CallConnectionStatus } from "./mediaTypes";

export type RealtimeCallClient = {
  connect(sessionId: string, localStream?: MediaStream): Promise<void>;
  disconnect(): Promise<void>;
  mute(muted: boolean): void;
  getStatus(): CallConnectionStatus;
  subscribe(listener: (status: CallConnectionStatus) => void): () => void;
};

export function createPlaceholderRealtimeCallClient(): RealtimeCallClient {
  let status: CallConnectionStatus = "idle";
  const listeners = new Set<(status: CallConnectionStatus) => void>();
  const setStatus = (next: CallConnectionStatus): void => {
    status = next;
    for (const listener of listeners) listener(status);
  };
  return {
    async connect(sessionId) {
      setStatus("connecting");
      const joinConfig = await getJoinConfig(sessionId).catch(() => null);
      if (joinConfig === null || joinConfig.status.includes("not_implemented")) {
        setStatus("not_available");
        return;
      }
      setStatus("connected");
    },
    disconnect() {
      setStatus("disconnected");
      return Promise.resolve();
    },
    mute(muted) {
      setStatus(muted ? "muted" : "microphone_ready");
    },
    getStatus() {
      return status;
    },
    subscribe(listener) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}
