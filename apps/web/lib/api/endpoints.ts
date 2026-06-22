export function productsEndpoint(): string {
  return "/api/v1/products";
}

export function productGuidanceEndpoint(productId: string): string {
  return `/api/v1/products/${encodeURIComponent(productId)}/guidance`;
}

export function productRecipesEndpoint(productId: string): string {
  return `/api/v1/products/${encodeURIComponent(productId)}/recipes`;
}

export function recipeValidateEndpoint(productId: string, recipeId: string): string {
  return `/api/v1/products/${encodeURIComponent(productId)}/recipes/${encodeURIComponent(recipeId)}/validate`;
}

export function demoSessionsEndpoint(): string {
  return "/api/v1/demo-sessions";
}

export function demoStartEndpoint(): string {
  return "/api/v1/demo/start";
}

export function metricsSummaryEndpoint(): string {
  return "/api/v1/metrics/summary";
}

export function demoSessionEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}`;
}

export function demoSessionStartEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/start`;
}

export function demoSessionPrewarmEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/prewarm`;
}

export function demoSessionEndEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/end`;
}

export function demoSessionRecoverEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/recover`;
}

export function demoSessionOrchestrationStateEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/orchestration-state`;
}

export function demoSessionStateEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/state`;
}

export function demoSessionJoinConfigEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/join-config`;
}

export function demoSessionEventsEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/events`;
}

export function demoSessionTextTurnEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/turns/text`;
}

export function transcriptEndpoint(sessionId: string): string {
  return `/api/v1/demo-sessions/${encodeURIComponent(sessionId)}/transcript`;
}
