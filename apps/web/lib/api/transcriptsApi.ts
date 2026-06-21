import type { TranscriptEventsResponse } from "@live-demo-agent/contracts";

import { apiRequest } from "./apiClient";
import { transcriptEndpoint } from "./endpoints";

export function getTranscript(sessionId: string): Promise<TranscriptEventsResponse> {
  return apiRequest<TranscriptEventsResponse>(transcriptEndpoint(sessionId));
}
