import type { EventConnectionStatus, LiveDemoEvent } from "./eventTypes";
import type { LiveEventClient } from "./eventClient";

export class WebSocketEventClient implements LiveEventClient {
  private status: EventConnectionStatus = "idle";

  connect(): void {
    this.status = "failed";
  }

  disconnect(): void {
    this.status = "disconnected";
  }

  subscribe(listener: (event: LiveDemoEvent) => void): () => void {
    void listener;
    return () => {
      // no-op until the websocket transport is implemented.
    };
  }

  subscribeStatus(listener: (status: EventConnectionStatus) => void): () => void {
    void listener;
    return () => {
      // no-op until the websocket transport is implemented.
    };
  }

  getStatus(): EventConnectionStatus {
    return this.status;
  }
}
