import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-vus",
      vus: 1,
      duration: "10s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const response = http.get(`${BASE_URL}/healthz`);
  check(response, {
    "health endpoint returned non-error": (res) => res.status < 500,
  });
}
