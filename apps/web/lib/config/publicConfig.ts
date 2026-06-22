export type EventTransport = "sse" | "websocket";
export type BrowserFrameMode = "screenshot" | "video" | "webrtc";

export type PublicConfig = {
  appName: string;
  apiBaseUrl: string;
  eventsBaseUrl: string;
  eventTransport: EventTransport;
  enableDebugPanel: boolean;
  enableMockEvents: boolean;
  enableWebrtcPlaceholder: boolean;
  browserFrameMode: BrowserFrameMode;
  maxEventBufferSize: number;
  maxTranscriptEvents: number;
  maxLatencySamples: number;
  frameStaleAfterMs: number;
  defaultProductUrl: string;
  maxEventPayloadBytes: number;
  grafanaUrl: string;
  prometheusUrl: string;
  jaegerUrl: string;
  lokiUrl: string;
  browserRuntimeUrl: string;
  agentRuntimeUrl: string;
  minioUrl: string;
  providerModeLabel: string;
};

type RuntimePublicConfig = Partial<Record<string, string>>;

export function getPublicConfig(): PublicConfig {
  return {
    appName: readString("NEXT_PUBLIC_APP_NAME", "Live Demo Agent"),
    apiBaseUrl: readString("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000"),
    eventsBaseUrl: readString("NEXT_PUBLIC_EVENTS_BASE_URL", "http://localhost:8000"),
    eventTransport: readEventTransport(process.env.NEXT_PUBLIC_EVENT_TRANSPORT),
    enableDebugPanel: readBoolean("NEXT_PUBLIC_ENABLE_DEBUG_PANEL", true),
    enableMockEvents: readBoolean("NEXT_PUBLIC_ENABLE_MOCK_EVENTS", false),
    enableWebrtcPlaceholder: readBoolean("NEXT_PUBLIC_ENABLE_WEBRTC_PLACEHOLDER", true),
    browserFrameMode: readBrowserFrameMode(process.env.NEXT_PUBLIC_BROWSER_FRAME_MODE),
    maxEventBufferSize: readInteger("NEXT_PUBLIC_MAX_EVENT_BUFFER_SIZE", 1000, 10, 5000),
    maxTranscriptEvents: readInteger("NEXT_PUBLIC_MAX_TRANSCRIPT_EVENTS", 500, 10, 2000),
    maxLatencySamples: readInteger("NEXT_PUBLIC_MAX_LATENCY_SAMPLES", 512, 10, 5000),
    frameStaleAfterMs: readInteger("NEXT_PUBLIC_FRAME_STALE_AFTER_MS", 10_000, 1000, 120_000),
    defaultProductUrl: readString("NEXT_PUBLIC_DEFAULT_PRODUCT_URL", "https://example.com"),
    maxEventPayloadBytes: readInteger("NEXT_PUBLIC_MAX_EVENT_PAYLOAD_BYTES", 262_144, 1024, 1_048_576),
    grafanaUrl: readString("NEXT_PUBLIC_GRAFANA_URL", "http://localhost:3001"),
    prometheusUrl: readString("NEXT_PUBLIC_PROMETHEUS_URL", "http://localhost:9090"),
    jaegerUrl: readString("NEXT_PUBLIC_JAEGER_URL", "http://localhost:16686"),
    lokiUrl: readString("NEXT_PUBLIC_LOKI_URL", "http://localhost:3100"),
    browserRuntimeUrl: readString("NEXT_PUBLIC_BROWSER_RUNTIME_URL", "http://localhost:8200"),
    agentRuntimeUrl: readString("NEXT_PUBLIC_AGENT_RUNTIME_URL", "http://localhost:8300"),
    minioUrl: readString("NEXT_PUBLIC_MINIO_URL", "http://localhost:9000"),
    providerModeLabel: readString("NEXT_PUBLIC_PROVIDER_MODE_LABEL", "Fake Providers"),
  };
}

function readString(key: string, fallback: string): string {
  const runtimeConfig = readRuntimePublicConfig();
  const value = runtimeConfig[key] ?? process.env[key];
  return value === undefined || value.trim() === "" ? fallback : value;
}

function readBoolean(key: string, fallback: boolean): boolean {
  const value = process.env[key];
  if (value === undefined || value.trim() === "") return fallback;
  return value.toLowerCase() === "true";
}

function readInteger(key: string, fallback: number, min: number, max: number): number {
  const value = process.env[key];
  const parsed = value === undefined || value.trim() === "" ? fallback : Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(min, Math.min(max, parsed));
}

function readEventTransport(value: string | undefined): EventTransport {
  return value === "websocket" ? "websocket" : "sse";
}

function readBrowserFrameMode(value: string | undefined): BrowserFrameMode {
  if (value === "video" || value === "webrtc") return value;
  return "screenshot";
}

function readRuntimePublicConfig(): RuntimePublicConfig {
  if (typeof window === "undefined") return {};
  const globalScope = window as Window & {
    __LIVE_DEMO_PUBLIC_CONFIG__?: RuntimePublicConfig;
  };
  return globalScope.__LIVE_DEMO_PUBLIC_CONFIG__ ?? {};
}
