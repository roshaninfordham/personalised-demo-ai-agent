import type { EventEnvelope } from "@live-demo-agent/contracts";

export type EventHandler = (event: EventEnvelope) => void;

export type EventClient = {
  connect: () => () => void;
};

export function createEventClient(sessionId: string, onEvent: EventHandler): EventClient {
  return {
    connect: () => {
      void sessionId;
      void onEvent;
      return () => undefined;
    },
  };
}
