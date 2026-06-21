export function nowIso(): string {
  return new Date().toISOString();
}

export function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "unknown";
  return new Intl.DateTimeFormat("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

export function formatClock(value: string): string {
  return formatTime(value);
}

export function eventLagMs(createdAt: string, receivedAtMs: number): number {
  const parsed = Date.parse(createdAt);
  if (!Number.isFinite(parsed)) return 0;
  return Math.max(0, receivedAtMs - parsed);
}
