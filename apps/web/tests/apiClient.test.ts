import { describe, expect, it, vi } from "vitest";

import { apiRequest } from "../lib/api/apiClient";
import { ApiClientError } from "../lib/api/apiErrors";

describe("apiRequest", () => {
  it("rejects absolute endpoints", async () => {
    await expect(apiRequest("https://evil.example")).rejects.toBeInstanceOf(ApiClientError);
  });

  it("adds request ID and parses JSON success", async () => {
    const fetchMock = vi.fn((_url: string | URL | Request, init?: RequestInit) => {
      expect(init?.headers).toMatchObject({ "X-Organization-ID": "00000000-0000-0000-0000-000000000001" });
      return Promise.resolve(
        new Response(JSON.stringify({ ok: true }), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiRequest<{ ok: boolean }>("/api/v1/test")).resolves.toEqual({ ok: true });
    vi.unstubAllGlobals();
  });

  it("normalizes API error envelope", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          new Response(
            JSON.stringify({
              error: {
                code: "product_not_found",
                message: "Product not found.",
                request_id: "req",
                trace_id: "trace",
                details: {},
              },
            }),
            { status: 404, headers: { "content-type": "application/json" } },
          ),
        ),
      ),
    );
    await expect(apiRequest("/api/v1/missing")).rejects.toMatchObject({
      apiError: { code: "product_not_found", status: 404 },
    });
    vi.unstubAllGlobals();
  });
});
