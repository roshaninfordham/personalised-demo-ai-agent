export function sessionCurrentScreenKey(prefix: string, sessionId: string): string {
  return `${prefix}:session:${sessionId}:current_screen`;
}

export function sessionSafeActionsKey(prefix: string, sessionId: string): string {
  return `${prefix}:session:${sessionId}:safe_actions`;
}

export function sessionBrowserStatusKey(prefix: string, sessionId: string): string {
  return `${prefix}:session:${sessionId}:browser_status`;
}

export function sessionEventsStreamKey(prefix: string, sessionId: string): string {
  return `${prefix}:stream:session:${sessionId}:events`;
}

export function globalEventsStreamKey(prefix: string): string {
  return `${prefix}:stream:global:events`;
}

