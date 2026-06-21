"use client";

import { useEffect, useMemo, useSyncExternalStore } from "react";

import { getPublicConfig } from "../lib/config/publicConfig";
import { SseEventClient } from "../lib/events/sseEventClient";
import { createMockEventReplay } from "../lib/events/eventReplay";
import { getOrCreateLiveDemoStore, type LiveDemoStore } from "../lib/events/eventStore";
import type { LiveDemoClientState } from "../lib/events/eventTypes";

export function useSessionEvents(sessionId: string): { state: LiveDemoClientState; store: LiveDemoStore } {
  const store = useMemo(() => getOrCreateLiveDemoStore(sessionId), [sessionId]);
  useEffect(() => {
    const config = getPublicConfig();
    if (config.enableMockEvents) {
      store.setConnectionStatus("connected");
      const timers = createMockEventReplay(sessionId).map((event, index) =>
        setTimeout(() => {
          store.dispatch(event);
        }, index * 250),
      );
      return () => {
        for (const timer of timers) clearTimeout(timer);
      };
    }
    const client = new SseEventClient();
    const unsubscribeEvents = client.subscribe((event) => {
      store.dispatch(event);
    });
    const unsubscribeStatus = client.subscribeStatus((status) => {
      store.setConnectionStatus(status);
    });
    client.connect(sessionId);
    return () => {
      unsubscribeEvents();
      unsubscribeStatus();
      client.disconnect();
    };
  }, [sessionId, store]);

  const state = useSyncExternalStore(
    (listener) => store.subscribe(listener),
    () => store.getSnapshot(),
    () => store.getSnapshot(),
  );
  return { state, store };
}
