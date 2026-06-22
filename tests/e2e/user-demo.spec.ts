import { expect, test, type Page } from "@playwright/test";

import { apiBaseUrl } from "./runtimeEnv";

const sessionId = "00000000-0000-0000-0000-000000000010";
const productId = "00000000-0000-0000-0000-000000000020";
const now = "2026-06-22T12:00:00.000Z";
const screenshot =
  "data:image/svg+xml;utf8," +
  encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="900">
  <rect width="1440" height="900" fill="#101827"/>
  <rect x="90" y="90" width="1260" height="130" rx="18" fill="#1f2937"/>
  <text x="130" y="170" fill="#f9fafb" font-size="58" font-family="Arial">Dashboard</text>
  <rect x="120" y="300" width="300" height="170" rx="16" fill="#4f46e5"/>
  <text x="155" y="390" fill="#ffffff" font-size="36" font-family="Arial">Revenue</text>
  <rect x="470" y="300" width="300" height="170" rx="16" fill="#111827" stroke="#374151"/>
  <text x="510" y="390" fill="#ffffff" font-size="36" font-family="Arial">Reports</text>
  <rect x="980" y="120" width="210" height="62" rx="12" fill="#10b981"/>
  <text x="1015" y="160" fill="#06121f" font-size="28" font-family="Arial">Add Metric</text>
</svg>`);

test("human-like local demo journey with safe browser action and grounded answer", async ({ page }) => {
  await installMockBackend(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Live AI Product Demo Agent" })).toBeVisible();
  await expect(page.getByLabel("Product URL")).toBeVisible();
  await expect(page.getByRole("link", { name: "Metrics & Analytics" }).first()).toBeVisible();

  await page.getByLabel("Product URL").fill("https://example.com");
  await page.getByRole("button", { name: "Add optional guidance" }).click();
  await page.getByLabel("Target persona").fill("founder");
  await page
    .getByLabel("Text guidance")
    .fill("Show dashboard, metric creation, and reports. Avoid delete and billing.");
  await page.getByRole("button", { name: "Start demo" }).click();

  await expect(page).toHaveURL(new RegExp(`/demo/${sessionId}$`));
  await expect(page.getByText("Controlled browser")).toBeVisible();
  await expect(page.getByTestId("browser-viewport")).toBeVisible();
  await expect(page.getByAltText(/Controlled browser: Dashboard/u)).toBeVisible();
  await expect(page.getByText("Learning sidebar")).toBeVisible();
  await expect(page.getByText("Found clickable actions")).toBeVisible();
  await expect(page.getByText("Call panel")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Transcript" })).toBeVisible();

  await expect(page.getByText("I'm a founder and I care about weekly revenue metrics.").first()).toBeVisible();
  await expect(page.getByText("I can show the visible dashboard and metric workflow.").first()).toBeVisible();
  await expect(
    page.getByText("I cannot verify Salesforce integration from the current evidence.").first(),
  ).toBeVisible();
  await expect(page.getByText("Delete Project was blocked by policy.").first()).toBeVisible();
  await expect(page.getByText("Salesforce integration exists")).toHaveCount(0);

  await expect(page.locator(".cursor-dot")).toBeVisible();
  await expect(page.locator(".highlight-box")).toBeVisible();
  await expect(page.locator(".ripple")).toBeVisible();
  await expect(page.getByText("browser.action.completed")).toBeVisible();
  await expect(page.getByText("browser.policy.blocked")).toBeVisible();
  await expect(page.getByText("lead_summary.ready")).toBeVisible();

  await page.getByRole("link", { name: "Metrics" }).click();
  await expect(page.getByRole("heading", { name: "Metrics & Analytics" })).toBeVisible();
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
    if (path.includes("/guidance") && request.method() === "POST") {
      await route.fulfill({ status: 201, headers: jsonHeaders(), body: JSON.stringify({ guidance_id: "guidance_1" }) });
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
        body: JSON.stringify({ session: demoSession("waiting_for_user"), join_config: joinConfig() }),
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
        body: events()
          .map((event) => `data: ${JSON.stringify(event)}\n\n`)
          .join(""),
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
    expires_at: "2026-06-22T13:00:00.000Z",
    status: "ready_for_signaling",
  };
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
    event(2, "browser.navigation.completed", {}),
    event(3, "browser.screen.updated", {
      screen_id: "screen_dashboard",
      screen_hash: "hash_dashboard",
      title: "Dashboard",
      url: "https://example.com",
      summary: "Dashboard with metrics and reports.",
      safe_action_count: 3,
      width: 1440,
      height: 900,
      image_url: screenshot,
    }),
    event(4, "session.live.started", {}),
    event(5, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000101",
      speaker: "user",
      chunk_type: "final",
      text: "I'm a founder and I care about weekly revenue metrics.",
      turn_id: "turn_1",
    }),
    event(6, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000102",
      speaker: "assistant",
      chunk_type: "final",
      text: "I can show the visible dashboard and metric workflow.",
      turn_id: "turn_1",
    }),
    event(7, "browser.cursor.move", { x: 1085, y: 150, duration_ms: 120 }),
    event(8, "browser.element.highlight", {
      element_id: "el_add_metric",
      label: "Add Metric",
      bbox: { x: 980, y: 120, width: 210, height: 62 },
      risk_level: "low",
      duration_ms: 5000,
    }),
    event(9, "browser.cursor.click", { x: 1085, y: 150 }),
    event(10, "browser.action.completed", { latency_ms: 220 }),
    event(11, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000103",
      speaker: "user",
      chunk_type: "final",
      text: "Does this integrate with Salesforce?",
      turn_id: "turn_2",
    }),
    event(12, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000104",
      speaker: "assistant",
      chunk_type: "final",
      text: "I cannot verify Salesforce integration from the current evidence.",
      turn_id: "turn_2",
    }),
    event(13, "browser.policy.blocked", { reason_code: "destructive_action", label: "Delete Project" }),
    event(14, "transcript.final", {
      transcript_event_id: "00000000-0000-0000-0000-000000000105",
      speaker: "assistant",
      chunk_type: "final",
      text: "Delete Project was blocked by policy.",
      turn_id: "turn_3",
    }),
    event(15, "learner.demo_graph.updated", {}),
    event(16, "lead_summary.ready", { summary_status: "ready" }),
    event(17, "session.ended", {}),
  ];
}

function jsonHeaders(): Record<string, string> {
  return { ...corsHeaders(), "content-type": "application/json" };
}

function corsHeaders(): Record<string, string> {
  return {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "*",
    "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
  };
}
