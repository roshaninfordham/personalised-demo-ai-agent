import type {
  CreateDemoRecipeRequest,
  DemoRecipeResponse,
  ValidateDemoRecipeResponse,
} from "@live-demo-agent/contracts";

import { apiRequest } from "./apiClient";
import { productRecipesEndpoint, recipeValidateEndpoint } from "./endpoints";

export function createDemoRecipe(productId: string, request: CreateDemoRecipeRequest): Promise<DemoRecipeResponse> {
  return apiRequest<DemoRecipeResponse>(productRecipesEndpoint(productId), { method: "POST", body: request });
}

export function validateDemoRecipe(productId: string, recipeId: string): Promise<ValidateDemoRecipeResponse> {
  return apiRequest<ValidateDemoRecipeResponse>(recipeValidateEndpoint(productId, recipeId), {
    method: "POST",
    body: {},
  });
}
