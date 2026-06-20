export type BrowserUseExploreInput = {
  productUrl: string;
  allowedDomains: string[];
};

export type BrowserUseExploreResult = {
  discoveredScreens: string[];
  candidateActions: string[];
  warnings: string[];
};

