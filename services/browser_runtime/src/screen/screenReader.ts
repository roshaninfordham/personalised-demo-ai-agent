import type { ScreenState } from "@live-demo-agent/contracts";

import type { BrowserRuntimeConfig } from "../config.js";
import type { ArtifactStore } from "../storage/artifactStore.js";
import type { LiveStateWriter } from "../redis/liveStateWriter.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import { recordScreenRead } from "../observability/browserInstrumentation.js";
import { checkLatencyBudget } from "../observability/latencyBudget.js";
import { extractAccessibilitySignature } from "./accessibilityExtractor.js";
import { extractDomSummary } from "./domExtractor.js";
import { extractRawElements } from "./elementExtractor.js";
import { normalizeScreen } from "./screenNormalizer.js";
import { captureAndStoreScreenshot } from "./screenshotCapturer.js";
import { extractVisibleText } from "./visibleTextExtractor.js";

export type ReadScreenOptions = {
  captureScreenshot: boolean;
};

export class ScreenReader {
  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly artifactStore: ArtifactStore,
    private readonly liveState: LiveStateWriter,
  ) {}

  async readCurrentScreen(
    session: BrowserSessionRecord,
    options: ReadScreenOptions,
  ): Promise<ScreenState> {
    const started = performance.now();
    const page = session.page;
    try {
      const url = page.url();
      const [titleResult, visibleTextResult, domSummaryResult, accessibilityResult, elementsResult] =
        await Promise.allSettled([
          page.title(),
          extractVisibleText(page, this.config.screenVisibleTextMaxChars),
          extractDomSummary(page, {
            maxNodes: this.config.domSummaryMaxNodes,
            maxTextPerNode: this.config.domSummaryMaxTextPerNode,
            maxArrayItems: this.config.domSummaryMaxArrayItems,
          }),
          extractAccessibilitySignature(
            page,
            this.config.accessibilityMaxNodes,
            this.config.accessibilityMaxDepth,
          ),
          extractRawElements(page, this.config.screenMaxElements),
        ]);
      const normalized = normalizeScreen({
        session,
        url,
        title: valueOr(titleResult, ""),
        visibleText: valueOr(visibleTextResult, ""),
        domSummary: valueOr(domSummaryResult, {
          counts: {},
          landmarks: [],
          headings: [],
          forms: [],
        }),
        accessibility: valueOr(accessibilityResult, []),
        rawElements: valueOr(elementsResult, []),
        screenshotUri: "",
        globalNeverClick: this.config.defaultNeverClick,
        actionScoreThreshold: this.config.actionExecutionScoreThreshold,
      });
      const artifact = options.captureScreenshot
        ? await captureAndStoreScreenshot(
            page,
            session,
            normalized.screenState.screen_id,
            this.config,
            this.artifactStore,
          ).catch(() => undefined)
        : undefined;
      normalized.screenState.screenshot_uri = artifact?.objectKey ?? "";
      session.currentScreenState = normalized.screenState;
      session.currentElements = new Map(
        normalized.elements.map((element) => [element.element_id, element]),
      );
      session.updatedAt = new Date().toISOString();
      await this.liveState.setCurrentScreen(session, normalized.screenState, artifact?.artifactId ?? null);
      await this.liveState.setSafeActions(session, session.currentSafeActions);
      const latencyMs = performance.now() - started;
      recordScreenRead("success", latencyMs);
      checkLatencyBudget("screen_read", latencyMs);
      return normalized.screenState;
    } catch (error) {
      const latencyMs = performance.now() - started;
      recordScreenRead("failed", latencyMs);
      checkLatencyBudget("screen_read", latencyMs);
      throw error;
    }
  }
}

function valueOr<T>(result: PromiseSettledResult<T>, fallback: T): T {
  return result.status === "fulfilled" ? result.value : fallback;
}
