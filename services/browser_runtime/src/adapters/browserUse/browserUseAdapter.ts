import { BrowserRuntimeError } from "../../errors.js";
import type { BrowserUseExploreInput, BrowserUseExploreResult } from "./browserUseTypes.js";

export class DisabledBrowserUseAdapter {
  exploreProduct(input: BrowserUseExploreInput): Promise<BrowserUseExploreResult> {
    void input;
    return Promise.reject(
      new BrowserRuntimeError(
        "browser_use_disabled",
        "browser-use background exploration is disabled.",
        501,
      ),
    );
  }

  assertNotHotPath(allowHotPath: boolean): void {
    if (!allowHotPath) {
      throw new BrowserRuntimeError(
        "browser_use_hot_path_blocked",
        "browser-use cannot run in the live hot path.",
        403,
      );
    }
  }
}
