import type { BrowserContext, Page } from "playwright";
import type { ScreenState } from "@live-demo-agent/contracts";

import type { InternalElement } from "../screen/elementExtractor.js";
import type { SafeActionInternal } from "../actions/actionRanker.js";

export type BrowserSessionStatus =
  | "created"
  | "starting"
  | "ready"
  | "navigating"
  | "active"
  | "closing"
  | "closed"
  | "failed";

export type BrowserSessionRecord = {
  browserSessionId: string;
  organizationId: string;
  demoSessionId: string;
  productId: string;
  allowedDomains: string[];
  status: BrowserSessionStatus;
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
  context: BrowserContext;
  page: Page;
  currentScreenState?: ScreenState;
  currentElements: Map<string, InternalElement>;
  currentSafeActions: SafeActionInternal[];
  lastActionAt?: string;
  actionInFlight: boolean;
  cursorPosition: { x: number; y: number };
  screenIdsByHash: Map<string, string>;
};

export type CreateBrowserSessionInput = {
  organizationId: string;
  demoSessionId: string;
  productId: string;
  viewport: { width: number; height: number };
  allowedDomains: string[];
  startUrl?: string;
};

