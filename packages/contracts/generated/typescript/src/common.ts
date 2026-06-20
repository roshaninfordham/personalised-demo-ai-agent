// Generated from packages/contracts/schemas. Do not edit manually.

export type UuidString = string;

export type IsoDateTimeString = string;

export type TraceId = string;

export type ProviderName = string;

export interface JsonObject {
  [key: string]: JsonValue;
}

export type JsonValue = string | number | boolean | null | JsonValue[] | JsonObject;

export type Metadata = JsonObject;

export type RiskLevel = "low" | "medium" | "high" | "blocked" | "unknown";

export type PolicyDecision = "allowed" | "blocked" | "confirmation_required";

export type DemoPhase = "created" | "prewarming" | "discovery" | "overview" | "core_workflow" | "deep_dive" | "q_and_a" | "summary" | "recovery" | "completed" | "failed";

export type SessionStatus = "created" | "prewarming" | "waiting_for_user" | "live" | "ending" | "completed" | "failed";

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type PaginationCursor = string;

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id: string;
  trace_id: string;
  details: Metadata;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

export interface ProductConfiguration {
  allowed_domains?: string[];
  default_never_click?: string[];
  demo_credentials_configured?: boolean;
  preferred_recipe_id?: UuidString;
  browser_viewport?: Metadata;
}

export interface ProductResponse {
  product_id: UuidString;
  product_name: string;
  product_url: string;
  default_persona?: string;
  product_summary?: string;
  confidence: number;
  configuration: ProductConfiguration;
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
}

export interface CreateProductRequest {
  product_name: string;
  product_url: string;
  default_persona?: string;
  product_summary?: string;
  configuration?: ProductConfiguration;
}

export interface UpdateProductRequest {
  product_name?: string;
  product_url?: string;
  default_persona?: string;
  product_summary?: string;
  configuration?: ProductConfiguration;
}

export interface ListProductsResponse {
  items: ProductResponse[];
  next_cursor: PaginationCursor | null;
}

export type ProductGuidanceType = "text" | "document" | "recipe" | "recording" | "objection_playbook" | "messaging" | "sales_script" | "product_positioning" | "forbidden_actions" | "setup_notes";

export interface ProductGuidanceResponse {
  guidance_id: UuidString;
  product_id: UuidString;
  guidance_type: ProductGuidanceType;
  title?: string;
  content: Metadata;
  source_uri?: string;
  created_at: IsoDateTimeString;
  updated_at: IsoDateTimeString;
}

export interface CreateProductGuidanceRequest {
  guidance_type: ProductGuidanceType;
  title?: string;
  content: Metadata;
  source_uri?: string;
}

export interface UpdateProductGuidanceRequest {
  guidance_type?: ProductGuidanceType;
  title?: string;
  content?: Metadata;
  source_uri?: string;
}

export interface ListProductGuidanceResponse {
  items: ProductGuidanceResponse[];
  next_cursor: PaginationCursor | null;
}
