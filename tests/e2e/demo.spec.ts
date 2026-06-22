import { expect, test, type Page } from "@playwright/test";

import { apiBaseUrl } from "./runtimeEnv";

const sessionId = "00000000-0000-0000-0000-000000000010";
const productId = "00000000-0000-0000-0000-000000000020";
const now = "2026-06-21T12:00:00.000Z";

test("full local demo UI flow with scripted grounded events", async ({ page }) => {
  await installMockBackend(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Live Demo Agent" })).toBeVisible();
  await page.getByRole("link", { name: "Start demo" }).click();
  await page.getByLabel("Product URL").fill("https://example.com");
  await page.getByRole("button", { name: "Start demo" }).click();

  await expect(page.getByText("Controlled browser")).toBeVisible();
  await expect(page.getByTestId("browser-viewport")).toBeVisible();
  await expect(page.getByText("Dashboard", { exact: true })).toBeVisible();
  await expect(page.getByText("Learning sidebar")).toBeVisible();
  await expect(page.getByText("Found clickable actions")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Transcript" })).toBeVisible();
  await expect(page.getByText("Latency debug")).toBeVisible();
  await expect(page.getByText("browser.action.completed")).toBeVisible();
  await expect(page.getByText("Salesforce integration exists")).toHaveCount(0);
  await expect(
    page.getByText("cannot verify Salesforce integration from the current evidence"),
  ).toHaveCount(2);
});

async function installMockBackend(page: Page): Promise<void> {
  await page.route(`${apiBaseUrl}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders() });
      return;
    }
    if (path === "/api/v1/products" && request.method() === "POST") {
      await route.fulfill({ status: 201, headers: jsonHeaders(), body: JSON.stringify(product()) });
      return;
    }
    if (path === "/api/v1/demo-sessions" && request.method() === "POST") {
      await route.fulfill({
        status: 201,
        headers: jsonHeaders(),
        body: JSON.stringify({ session: demoSession("created") }),
      });
      return;
    }
    if (path.endsWith(`/demo-sessions/${sessionId}/start`) && request.method() === "POST") {
      await route.fulfill({
        status: 200,
        headers: jsonHeaders(),
        body: JSON.stringify({
          session: demoSession("waiting_for_user"),
          join_config: joinConfig(),
        }),
      });
      return;
    }
    if (path.endsWith(`/demo-sessions/${sessionId}/state`)) {
      await route.fulfill({
        status: 200,
        headers: jsonHeaders(),
        body: JSON.stringify({
          session: demoSession("live"),
          live_state: {
            available: true,
            current_screen: { title: "Dashboard" },
            safe_actions: [],
            browser_status: {},
            latency: {},
          },
        }),
      });
      return;
    }
    if (path.endsWith(`/demo-sessions/${sessionId}/events`)) {
      await route.fulfill({
        status: 200,
        headers: { ...corsHeaders(), "content-type": "text/event-stream" },
        body: eventStreamBody(),
      });
      return;
    }
    await route.fulfill({
      status: 404,
      headers: jsonHeaders(),
      body: JSON.stringify({ message: "not mocked" }),
    });
  });
}

function product() {
  return {
    product_id: productId,
    product_name: "Example Product",
    product_url: "https://example.com",
    confidence: 1,
    configuration: {},
    created_at: now,
    updated_at: now,
  };
}

function demoSession(status: string) {
  return {
    session_id: sessionId,
    product_id: productId,
    start_url: "https://example.com",
    status,
    current_phase: "overview",
    product_name: "Example Product",
    created_at: now,
    updated_at: now,
  };
}

function joinConfig() {
  return {
    transport_provider: "fake",
    session_id: sessionId,
    room_id: "room_test",
    join_token: null,
    expires_at: "2026-06-21T13:00:00.000Z",
    status: "ready_for_signaling",
  };
}

function eventStreamBody(): string {
  return events()
    .map((event) => `data: ${JSON.stringify(event)}\n\n`)
    .join("");
}

function events() {
  const event = (index: number, eventType: string, payload: Record<string, unknown>) => ({
    event_id: `00000000-0000-0000-0000-${String(index).padStart(12, "0")}`,
    session_id: sessionId,
    organization_id: "00000000-0000-0000-0000-000000000001",
    event_type: eventType,
    created_at: new Date(Date.parse(now) + index * 100).toISOString(),
    trace_id: `trace_${index}`,
    payload,
  });
  return [
    event(1, "session.prewarming.started", {}),
    event(2, "browser.screen.updated", {
      screen_id: "screen_dashboard",
      screen_hash: "hash_dashboard",
      title: "Dashboard",
      url: "https://example.com",
      summary: "Dashboard with metrics and reports.",
      safe_action_count: 3,
      width: 1440,
      height: 900,
    }),
    event(3, "browser.cursor.move", { x: 480, y: 240, duration_ms: 100 }),
    event(4, "browser.element.highlight", {
      element_id: "el_add_metric",
      label: "Add Metric",
      bbox: { x: 420, y: 210, width: 140, height: 42 },
      risk_level: "low",
    }),
    event(5, "browser.cursor.click", { x: 480, y: 240 }),
    event(6, "browser.action.completed", { latency_ms: 180 }),
    event(7, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000101",
      speaker: "user",
      chunk_type: "final",
      text: "Can this integrate with Salesforce?",
      turn_id: "turn_1",
    }),
    event(8, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000102",
      speaker: "assistant",
      chunk_type: "final",
      text: "I cannot verify Salesforce integration from the current evidence.",
      turn_id: "turn_1",
    }),
    event(9, "learner.screen_summary.ready", {}),
    event(10, "learner.demo_graph.updated", {}),
  ];
}

function jsonHeaders(): Record<string, string> {
  return { ...corsHeaders(), "content-type": "application/json" };
}

function corsHeaders(): Record<string, string> {
  return { "access-control-allow-origin": "*", "access-control-allow-headers": "*" };
}
