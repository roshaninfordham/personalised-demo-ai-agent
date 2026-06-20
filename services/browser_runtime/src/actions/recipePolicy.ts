export type RecipePolicy = {
  neverClick: string[];
  allowedActions: string[];
};

export function emptyRecipePolicy(): RecipePolicy {
  return { neverClick: [], allowedActions: [] };
}

