import type { CreateProductGuidanceRequest, ProductGuidanceResponse } from "@live-demo-agent/contracts";

import { apiRequest } from "./apiClient";
import { productGuidanceEndpoint } from "./endpoints";

export function createProductGuidance(
  productId: string,
  request: CreateProductGuidanceRequest,
): Promise<ProductGuidanceResponse> {
  return apiRequest<ProductGuidanceResponse>(productGuidanceEndpoint(productId), {
    method: "POST",
    body: request,
  });
}
