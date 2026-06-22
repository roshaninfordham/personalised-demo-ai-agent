import http from "k6/http";
import { check, sleep } from "k6";
import { Trend } from "k6/metrics";

export const prewarmDuration = new Trend("prewarm_duration");
export const sessionEndDuration = new Trend("session_end_duration");

export const options = {
  scenarios: {
    local_lifecycle: {
      executor: "constant-vus",
      vus: Number(__ENV.VUS || 5),
      duration: __ENV.DURATION || "5m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
    prewarm_duration: ["p(95)<8000"],
    session_end_duration: ["p(95)<15000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const ORG_ID = "00000000-0000-0000-0000-000000000001";
const headers = { "Content-Type": "application/json", "X-Organization-ID": ORG_ID };

export default function () {
  const product = http.post(
    `${BASE_URL}/api/v1/products`,
    JSON.stringify({
      product_name: `Load Product ${__VU}`,
      product_url: "https://example.com",
      default_persona: "founder",
    }),
    { headers },
  );
  check(product, { "product created": (res) => res.status < 500 });

  const productId = product.json("product_id") || "00000000-0000-0000-0000-000000000001";
  const session = http.post(
    `${BASE_URL}/api/v1/demo-sessions`,
    JSON.stringify({
      product_id: productId,
      start_url: "https://example.com",
      user_persona: "founder",
    }),
    { headers },
  );
  check(session, { "session created": (res) => res.status < 500 });
  const sessionId = session.json("session_id");
  if (!sessionId) {
    return;
  }

  const prewarmStart = Date.now();
  const prewarm = http.post(`${BASE_URL}/api/v1/demo-sessions/${sessionId}/prewarm`, null, {
    headers,
  });
  prewarmDuration.add(Date.now() - prewarmStart);
  check(prewarm, { "prewarm controlled": (res) => res.status < 500 });

  const start = http.post(`${BASE_URL}/api/v1/demo-sessions/${sessionId}/start`, null, {
    headers,
  });
  check(start, { "start controlled": (res) => res.status < 500 });

  sleep(1);

  const endStart = Date.now();
  const end = http.post(`${BASE_URL}/api/v1/demo-sessions/${sessionId}/end`, null, {
    headers,
  });
  sessionEndDuration.add(Date.now() - endStart);
  check(end, { "end controlled": (res) => res.status < 500 });
}
