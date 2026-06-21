export type CallConnectionStatus =
  | "idle"
  | "requesting_microphone"
  | "microphone_ready"
  | "connecting"
  | "connected"
  | "muted"
  | "reconnecting"
  | "disconnected"
  | "failed"
  | "not_available";
