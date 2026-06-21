import type { EventConnectionStatus, LiveDemoEvent } from "./eventTypes";

export type LiveEventClient = {
  connect(sessionId: string): void;
  disconnect(): void;
  subscribe(listener: (event: LiveDemoEvent) => void): () => void;
  subscribeStatus(listener: (status: EventConnectionStatus) => void): () => void;
  getStatus(): EventConnectionStatus;
};
