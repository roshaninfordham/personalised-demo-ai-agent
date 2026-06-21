import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type {
  CreateDemoRecipeRequest,
  CreateDemoSessionRequest,
  CreateProductGuidanceRequest,
  CreateProductRequest,
  ProductResponse,
} from "@live-demo-agent/contracts";
import { describe, expect, it, vi } from "vitest";

import { DemoStartForm, type DemoStartApi } from "../components/demo-start/DemoStartForm";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

describe("DemoStartForm", () => {
  it("renders required product URL field and validates missing URL", async () => {
    render(<DemoStartForm api={createApi([])} />);
    const url = screen.getByLabelText("Product URL");
    fireEvent.change(url, { target: { value: "" } });
    fireEvent.submit(screen.getByRole("button", { name: "Start demo" }).closest("form") as HTMLFormElement);
    expect(await screen.findAllByText("Product URL is required.")).toHaveLength(2);
  });

  it("rejects dangerous URL schemes", async () => {
    render(<DemoStartForm api={createApi([])} />);
    fireEvent.change(screen.getByLabelText("Product URL"), { target: { value: "javascript:alert(1)" } });
    expect(await screen.findByText("Use an http or https URL.")).toBeInTheDocument();
  });

  it("parses recipe JSON and calls APIs in order", async () => {
    const calls: string[] = [];
    let navigatedTo = "";
    render(
      <DemoStartForm
        api={createApi(calls)}
        onNavigate={(path) => {
          navigatedTo = path;
        }}
      />,
    );

    fireEvent.change(screen.getByLabelText("Product URL"), { target: { value: "https://example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Add optional guidance" }));
    fireEvent.change(screen.getByLabelText("Product name"), { target: { value: "Example Product" } });
    fireEvent.change(screen.getByLabelText("Target persona"), { target: { value: "founder" } });
    fireEvent.change(screen.getByLabelText("Text guidance"), { target: { value: "Focus on metrics." } });
    fireEvent.change(screen.getByLabelText("Recipe JSON"), {
      target: {
        value:
          '{"recipe_name":"Demo","demo_goal":"Show value","steps":[{"step_order":0,"step_key":"overview","goal":"Show overview"}]}',
      },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Start demo" }).closest("form") as HTMLFormElement);

    await waitFor(() => {
      expect(navigatedTo).toBe("/demo/00000000-0000-0000-0000-000000000010");
    });
    expect(calls).toEqual(["product", "guidance", "recipe", "validate", "session", "start"]);
  });

  it("prevents duplicate submit while pending", async () => {
    const calls: string[] = [];
    const api = createApi(calls, 50);
    render(<DemoStartForm api={api} />);
    fireEvent.change(screen.getByLabelText("Product URL"), { target: { value: "https://example.com" } });
    const form = screen.getByRole("button", { name: "Start demo" }).closest("form") as HTMLFormElement;
    fireEvent.submit(form);
    fireEvent.submit(form);
    await waitFor(() => {
      expect(calls.filter((call) => call === "product")).toHaveLength(1);
    });
  });

  it("handles partial guidance failure and still starts session", async () => {
    const calls: string[] = [];
    const api = createApi(calls);
    api.createProductGuidance = (productId: string, request: CreateProductGuidanceRequest) => {
      void productId;
      void request;
      calls.push("guidance");
      return Promise.reject(new Error("guidance failed"));
    };
    let navigatedTo = "";
    render(
      <DemoStartForm
        api={api}
        onNavigate={(path) => {
          navigatedTo = path;
        }}
      />,
    );
    fireEvent.change(screen.getByLabelText("Product URL"), { target: { value: "https://example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Add optional guidance" }));
    fireEvent.change(screen.getByLabelText("Text guidance"), { target: { value: "Focus on metrics." } });
    fireEvent.submit(screen.getByRole("button", { name: "Start demo" }).closest("form") as HTMLFormElement);
    await waitFor(() => {
      expect(navigatedTo).toBe("/demo/00000000-0000-0000-0000-000000000010");
    });
    expect(screen.getByText("Guidance could not be saved. Continuing without guidance.")).toBeInTheDocument();
  });
});

function createApi(calls: string[], delayMs = 0): DemoStartApi {
  const product: ProductResponse = {
    product_id: "00000000-0000-0000-0000-000000000020",
    product_name: "Example",
    product_url: "https://example.com/",
    confidence: 0,
    configuration: {},
    created_at: "2026-06-20T12:00:00.000Z",
    updated_at: "2026-06-20T12:00:00.000Z",
  };
  return {
    async createProduct(request: CreateProductRequest) {
      void request;
      calls.push("product");
      await sleep(delayMs);
      return product;
    },
    createProductGuidance(productId: string, request: CreateProductGuidanceRequest) {
      void productId;
      void request;
      calls.push("guidance");
      return Promise.resolve({
        guidance_id: "00000000-0000-0000-0000-000000000030",
        product_id: product.product_id,
        guidance_type: "text",
        content: {},
        created_at: "2026-06-20T12:00:00.000Z",
        updated_at: "2026-06-20T12:00:00.000Z",
      });
    },
    createDemoRecipe(productId: string, request: CreateDemoRecipeRequest) {
      void productId;
      void request;
      calls.push("recipe");
      return Promise.resolve({
        recipe_id: "00000000-0000-0000-0000-000000000040",
        product_id: product.product_id,
        recipe_name: "Demo",
        demo_goal: "Show value",
        status: "draft",
        is_active: false,
        steps: [],
        never_click: [],
        created_at: "2026-06-20T12:00:00.000Z",
        updated_at: "2026-06-20T12:00:00.000Z",
      });
    },
    validateDemoRecipe(productId: string, recipeId: string) {
      void productId;
      void recipeId;
      calls.push("validate");
      return Promise.resolve({ valid: true, errors: [], warnings: [] });
    },
    createDemoSession(request: CreateDemoSessionRequest) {
      void request;
      calls.push("session");
      return Promise.resolve({
        session: {
          session_id: "00000000-0000-0000-0000-000000000010",
          product_id: product.product_id,
          start_url: product.product_url,
          status: "created",
          current_phase: "created",
          created_at: "2026-06-20T12:00:00.000Z",
          updated_at: "2026-06-20T12:00:00.000Z",
        },
      });
    },
    startDemoSession(sessionId: string) {
      void sessionId;
      calls.push("start");
      return Promise.resolve({
        session: {
          session_id: "00000000-0000-0000-0000-000000000010",
          product_id: product.product_id,
          start_url: product.product_url,
          status: "prewarming",
          current_phase: "prewarming",
          created_at: "2026-06-20T12:00:00.000Z",
          updated_at: "2026-06-20T12:00:00.000Z",
        },
        join_config: {
          transport_provider: "small_webrtc",
          session_id: "00000000-0000-0000-0000-000000000010",
          room_id: "local-placeholder",
          join_token: null,
          expires_at: "2026-06-20T13:00:00.000Z",
          status: "not_implemented_in_phase_3",
        },
      });
    },
  };
}

function sleep(delayMs: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, delayMs));
}
