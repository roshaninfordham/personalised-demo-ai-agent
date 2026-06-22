import { redactRecord } from "../logger.js";

export function buildLogPayload(
  eventType: string,
  fields: Record<string, unknown>,
): Record<string, unknown> {
  return redactRecord({
    event_type: eventType,
    service: "browser-runtime",
    environment: process.env.DEPLOYMENT_ENVIRONMENT ?? process.env.APP_ENV ?? "local",
    ...fields,
  });
}
