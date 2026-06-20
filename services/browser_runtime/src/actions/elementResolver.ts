import type { Locator } from "playwright";

import { BrowserRuntimeError } from "../errors.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import type { InternalElement } from "../screen/elementExtractor.js";

export type ResolvedElement = {
  element: InternalElement;
  locator: Locator;
};

export function resolveElement(session: BrowserSessionRecord, elementId: string): ResolvedElement {
  const element = session.currentElements.get(elementId);
  if (element === undefined) {
    throw new BrowserRuntimeError("stale_element", "Element is not available on the current screen.", 409);
  }
  return {
    element,
    locator: session.page.locator(element.selectorHint).first(),
  };
}

