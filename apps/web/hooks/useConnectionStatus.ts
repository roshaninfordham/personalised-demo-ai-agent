"use client";

import type { EventConnectionStatus } from "../lib/events/eventTypes";

export function useConnectionStatus(status: EventConnectionStatus): EventConnectionStatus {
  return status;
}
