const publicKeys = [
  "NEXT_PUBLIC_APP_NAME",
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_EVENTS_BASE_URL",
  "NEXT_PUBLIC_EVENT_TRANSPORT",
  "NEXT_PUBLIC_ENABLE_DEBUG_PANEL",
  "NEXT_PUBLIC_ENABLE_MOCK_EVENTS",
  "NEXT_PUBLIC_ENABLE_MOCK_DEMO",
  "NEXT_PUBLIC_ENABLE_WEBRTC_PLACEHOLDER",
  "NEXT_PUBLIC_BROWSER_FRAME_MODE",
  "NEXT_PUBLIC_MAX_EVENT_BUFFER_SIZE",
  "NEXT_PUBLIC_MAX_TRANSCRIPT_EVENTS",
  "NEXT_PUBLIC_MAX_LATENCY_SAMPLES",
  "NEXT_PUBLIC_FRAME_STALE_AFTER_MS",
  "NEXT_PUBLIC_DEFAULT_PRODUCT_URL",
  "NEXT_PUBLIC_MAX_EVENT_PAYLOAD_BYTES",
  "NEXT_PUBLIC_GRAFANA_URL",
  "NEXT_PUBLIC_PROMETHEUS_URL",
  "NEXT_PUBLIC_JAEGER_URL",
  "NEXT_PUBLIC_LOKI_URL",
  "NEXT_PUBLIC_BROWSER_RUNTIME_URL",
  "NEXT_PUBLIC_AGENT_RUNTIME_URL",
  "NEXT_PUBLIC_MINIO_URL",
  "NEXT_PUBLIC_PROVIDER_MODE_LABEL",
] as const;

export function GET(): Response {
  const config = Object.fromEntries(
    publicKeys.map((key) => [key, process.env[key] ?? ""]),
  );
  const body = `window.__LIVE_DEMO_PUBLIC_CONFIG__ = ${JSON.stringify(config)};\n`;
  return new Response(body, {
    headers: {
      "cache-control": "no-store",
      "content-type": "application/javascript; charset=utf-8",
    },
  });
}
