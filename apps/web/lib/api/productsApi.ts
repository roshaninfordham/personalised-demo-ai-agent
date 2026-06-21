import type { CreateProductRequest, ProductResponse } from "@live-demo-agent/contracts";

import { apiRequest } from "./apiClient";
import { productsEndpoint } from "./endpoints";

export function createProduct(request: CreateProductRequest): Promise<ProductResponse> {
  return apiRequest<ProductResponse>(productsEndpoint(), { method: "POST", body: request });
}
