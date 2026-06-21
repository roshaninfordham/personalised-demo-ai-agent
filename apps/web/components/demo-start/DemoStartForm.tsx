"use client";

import { useMemo, useState, type SyntheticEvent } from "react";
import { useRouter } from "next/navigation";
import type {
  CreateDemoRecipeRequest,
  CreateDemoSessionRequest,
  CreateProductGuidanceRequest,
  CreateProductRequest,
  ProductResponse,
} from "@live-demo-agent/contracts";

import { createDemoSession, startDemoSession } from "../../lib/api/demoSessionsApi";
import { createProductGuidance } from "../../lib/api/guidanceApi";
import { createProduct } from "../../lib/api/productsApi";
import { createDemoRecipe, validateDemoRecipe } from "../../lib/api/recipesApi";
import { getPublicConfig } from "../../lib/config/publicConfig";
import { validateGuidance } from "../../lib/validation/guidanceValidation";
import { validateProductUrl } from "../../lib/validation/productUrlValidation";
import { validateRecipeJson } from "../../lib/validation/recipeJsonValidation";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { GuidanceTextarea } from "./GuidanceTextarea";
import { RecipeJsonEditor } from "./RecipeJsonEditor";
import { UrlInput } from "./UrlInput";

export type DemoStartApi = {
  createProduct: typeof createProduct;
  createProductGuidance: typeof createProductGuidance;
  createDemoRecipe: typeof createDemoRecipe;
  validateDemoRecipe: typeof validateDemoRecipe;
  createDemoSession: typeof createDemoSession;
  startDemoSession: typeof startDemoSession;
};

const defaultApi: DemoStartApi = {
  createProduct,
  createProductGuidance,
  createDemoRecipe,
  validateDemoRecipe,
  createDemoSession,
  startDemoSession,
};

type FormState =
  | "idle"
  | "creating_product"
  | "saving_guidance"
  | "saving_recipe"
  | "creating_session"
  | "starting_session"
  | "navigating_to_session"
  | "failed";

export function DemoStartForm({
  api = defaultApi,
  onNavigate,
}: {
  api?: DemoStartApi;
  onNavigate?: (path: string) => void;
}) {
  const router = useRouter();
  const config = getPublicConfig();
  const [productUrl, setProductUrl] = useState(config.defaultProductUrl);
  const [productName, setProductName] = useState("");
  const [targetPersona, setTargetPersona] = useState("");
  const [textGuidance, setTextGuidance] = useState("");
  const [recipeJson, setRecipeJson] = useState("");
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [formState, setFormState] = useState<FormState>("idle");
  const [formError, setFormError] = useState<string | null>(null);
  const [partialWarning, setPartialWarning] = useState<string | null>(null);

  const urlValidation = useMemo(() => validateProductUrl(productUrl), [productUrl]);
  const guidanceValidation = useMemo(() => validateGuidance(textGuidance), [textGuidance]);
  const recipeValidation = useMemo(() => validateRecipeJson(recipeJson), [recipeJson]);

  const urlError = urlValidation.valid ? null : (urlValidation.error ?? "Enter a valid URL.");
  const guidanceError = guidanceValidation.valid ? null : (guidanceValidation.error ?? "Guidance is invalid.");
  const recipeError = recipeValidation.valid ? null : recipeValidation.errors[0] ?? "Recipe JSON is invalid.";
  const submitting = formState !== "idle" && formState !== "failed";

  function navigate(path: string): void {
    if (onNavigate !== undefined) {
      onNavigate(path);
      return;
    }
    router.push(path);
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (submitting) return;
    setFormError(null);
    setPartialWarning(null);
    if (!urlValidation.valid || urlValidation.normalizedUrl === undefined) {
      setFormError(urlError);
      return;
    }
    if (!guidanceValidation.valid) {
      setFormError(guidanceError);
      return;
    }
    if (!recipeValidation.valid) {
      setFormError(recipeError);
      return;
    }

    try {
      setFormState("creating_product");
      const productRequest: CreateProductRequest = {
        product_name: productName.trim() || productNameFromUrl(urlValidation.normalizedUrl),
        product_url: urlValidation.normalizedUrl,
      };
      if (targetPersona.trim() !== "") productRequest.default_persona = targetPersona.trim();
      const product = await api.createProduct(productRequest);

      if (textGuidance.trim() !== "") {
        setFormState("saving_guidance");
        await createGuidanceWithWarning(api, product, textGuidance, setPartialWarning);
      }

      const recipeId = await maybeCreateRecipe(api, product.product_id, recipeJson, recipeValidation.parsed, setPartialWarning);

      setFormState("creating_session");
      const sessionRequest: CreateDemoSessionRequest = {
        product_id: product.product_id,
        start_url: urlValidation.normalizedUrl,
      };
      if (recipeId !== null) sessionRequest.recipe_id = recipeId;
      if (targetPersona.trim() !== "") sessionRequest.user_persona = targetPersona.trim();
      const sessionResponse = await api.createDemoSession(sessionRequest);

      setFormState("starting_session");
      await api.startDemoSession(sessionResponse.session.session_id);

      setFormState("navigating_to_session");
      navigate(`/demo/${sessionResponse.session.session_id}`);
    } catch (error: unknown) {
      setFormState("failed");
      setFormError(error instanceof Error ? error.message : "Demo session could not be started.");
    }
  }

  return (
    <form className="stack" onSubmit={(event) => void handleSubmit(event)} noValidate>
      <UrlInput value={productUrl} onChange={setProductUrl} error={urlError} warning={urlValidation.warning ?? null} />

      <button
        type="button"
        className="button button-secondary"
        onClick={() => {
          setAdvancedOpen((current) => !current);
        }}
        aria-expanded={advancedOpen}
      >
        {advancedOpen ? "Hide optional guidance" : "Add optional guidance"}
      </button>

      {advancedOpen ? (
        <div className="advanced-panel stack">
          <div className="field">
            <label htmlFor="product-name">Product name</label>
            <Input
              id="product-name"
              value={productName}
              onChange={(event) => {
                setProductName(event.target.value);
              }}
              placeholder="Example Analytics"
            />
          </div>
          <div className="field">
            <label htmlFor="target-persona">Target persona</label>
            <Input
              id="target-persona"
              value={targetPersona}
              onChange={(event) => {
                setTargetPersona(event.target.value);
              }}
              placeholder="founder"
            />
          </div>
          <GuidanceTextarea value={textGuidance} onChange={setTextGuidance} error={guidanceError} />
          <RecipeJsonEditor value={recipeJson} onChange={setRecipeJson} error={recipeError} />
        </div>
      ) : null}

      {partialWarning === null ? null : <div className="field-warning">{partialWarning}</div>}
      {formError === null ? null : <div className="error-banner">{formError}</div>}

      <div className="row">
        <Button type="submit" disabled={submitting || urlError !== null}>
          {submitLabel(formState)}
        </Button>
        <span className="muted">Frontend validation is UX only. Backend validation is authoritative.</span>
      </div>
    </form>
  );
}

async function createGuidanceWithWarning(
  api: DemoStartApi,
  product: ProductResponse,
  textGuidance: string,
  setPartialWarning: (message: string) => void,
): Promise<void> {
  const request: CreateProductGuidanceRequest = {
    guidance_type: "text",
    title: "Frontend start guidance",
    content: { text: textGuidance.trim() },
  };
  try {
    await api.createProductGuidance(product.product_id, request);
  } catch {
    setPartialWarning("Guidance could not be saved. Continuing without guidance.");
  }
}

async function maybeCreateRecipe(
  api: DemoStartApi,
  productId: string,
  recipeJson: string,
  parsed: Record<string, unknown> | undefined,
  setPartialWarning: (message: string) => void,
): Promise<string | null> {
  if (recipeJson.trim() === "" || parsed === undefined) return null;
  const request = toCreateRecipeRequest(parsed);
  try {
    const recipe = await api.createDemoRecipe(productId, request);
    await api.validateDemoRecipe(productId, recipe.recipe_id);
    return recipe.recipe_id;
  } catch {
    setPartialWarning("Recipe could not be saved. Continuing without a recipe.");
    return null;
  }
}

function toCreateRecipeRequest(parsed: Record<string, unknown>): CreateDemoRecipeRequest {
  const steps = Array.isArray(parsed.steps) ? parsed.steps : [];
  const request: CreateDemoRecipeRequest = {
    recipe_name: stringField(parsed.recipe_name) ?? "Frontend supplied recipe",
    demo_goal: stringField(parsed.demo_goal) ?? "Run a guided product demo.",
    steps: steps.map((step, index) => {
      if (!isRecord(step)) {
        return { step_order: index, step_key: `step_${String(index)}`, goal: "Review screen" };
      }
      const item: CreateDemoRecipeRequest["steps"][number] = {
        step_order: numberField(step.step_order) ?? index,
        step_key: stringField(step.step_key) ?? `step_${String(index)}`,
        goal: stringField(step.goal) ?? "Review screen",
      };
      const screenHint = stringField(step.screen_hint);
      if (screenHint !== undefined) item.screen_hint = screenHint;
      const clickHint = stringField(step.click_hint);
      if (clickHint !== undefined) item.click_hint = clickHint;
      const talkTrack = stringField(step.talk_track);
      if (talkTrack !== undefined) item.talk_track = talkTrack;
      const allowedActions = stringArray(step.allowed_actions);
      if (allowedActions !== undefined) item.allowed_actions = allowedActions;
      const successCriteria = stringArray(step.success_criteria);
      if (successCriteria !== undefined) item.success_criteria = successCriteria;
      const fallbackStrategy = stringField(step.fallback_strategy);
      if (fallbackStrategy !== undefined) item.fallback_strategy = fallbackStrategy;
      return item;
    }),
  };
  const targetPersona = stringField(parsed.target_persona);
  if (targetPersona !== undefined) request.target_persona = targetPersona;
  const globalTalkTrack = stringField(parsed.global_talk_track);
  if (globalTalkTrack !== undefined) request.global_talk_track = globalTalkTrack;
  const neverClick = stringArray(parsed.never_click);
  if (neverClick !== undefined) request.never_click = neverClick;
  return request;
}

function productNameFromUrl(url: string): string {
  return new URL(url).hostname.replace(/^www\./, "");
}

function submitLabel(state: FormState): string {
  switch (state) {
    case "idle":
    case "failed":
      return "Start demo";
    case "creating_product":
      return "Creating product...";
    case "saving_guidance":
      return "Saving guidance...";
    case "saving_recipe":
      return "Saving recipe...";
    case "creating_session":
      return "Creating session...";
    case "starting_session":
      return "Starting session...";
    case "navigating_to_session":
      return "Opening session...";
  }
}

function stringField(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() !== "" ? value.trim() : undefined;
}

function numberField(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function stringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const items = value.filter((item): item is string => typeof item === "string");
  return items.length === 0 ? undefined : items;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
