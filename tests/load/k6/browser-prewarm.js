import http from "k6/http";
import { check } from "k6";
import { Trend } from "k6/metrics";

export const prewarmDuration = new Trend("prewarm_duration");

export const options = {
  scenarios: {
    browser_prewarm: {
      executor: "constant-vus",
      vus: Number(__ENV.VUS || 3),
      duration: __ENV.DURATION || "2m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    prewarm_duration: ["p(95)<10000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ORG_ID = "00000000-0000-0000-0000-000000000001";
const headers = { "Content-Type": "application/json", "X-Organization-ID": ORG_ID };

export default function () {
  const sessionId = __ENV.SESSION_ID;
  if (!sessionId) {
    const response = http.get(`${BASE_URL}/healthz`);
    check(response, { "health endpoint controlled": (res) => res.status < 500 });
    return;
  }
  const started = Date.now();
  const response = http.post(`${BASE_URL}/api/v1/demo-sessions/${sessionId}/prewarm`, null, {
    headers,
  });
  prewarmDuration.add(Date.now() - started);
  check(response, { "prewarm controlled": (res) => res.status < 500 });
}
