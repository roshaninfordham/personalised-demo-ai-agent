import { z } from "zod";

export const uuidSchema = z.string().uuid();
export const browserSessionIdSchema = z.string().uuid();

export const viewportSchema = z.object({
  width: z.number().int().min(800).max(2560),
  height: z.number().int().min(600).max(1600),
});

export const createBrowserSessionRequestSchema = z.object({
  organization_id: uuidSchema,
  demo_session_id: uuidSchema,
  product_id: uuidSchema,
  viewport: viewportSchema.optional(),
  allowed_domains: z.array(z.string().min(1)).max(20).default([]),
  start_url: z.string().url().optional(),
  storage_state: z.null().optional(),
});

export const navigateRequestSchema = z.object({
  url: z.string().url(),
});

export const actionRequestSchema = z.object({
  command_id: uuidSchema.optional(),
  session_id: uuidSchema.optional(),
  action_type: z
    .enum([
      "read_current_screen",
      "highlight_element",
      "click_element",
      "type_into_element",
      "scroll",
      "go_back",
      "navigate_to_allowed_url",
      "wait_for_idle",
      "take_screenshot",
    ])
    .optional(),
  element_id: z.string().optional(),
  text: z.string().max(4000).optional(),
  direction: z.enum(["up", "down", "left", "right"]).optional(),
  url: z.string().url().optional(),
  requires_cursor_animation: z.boolean().optional(),
  policy_context: z.record(z.unknown()).optional(),
  user_confirmed: z.boolean().optional(),
});

export function parseBody<T>(schema: z.ZodType<T>, body: unknown): T {
  return schema.parse(body);
}

