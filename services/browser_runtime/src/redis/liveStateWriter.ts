import type { ScreenState } from "@live-demo-agent/contracts";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import type { SafeActionInternal } from "../actions/actionRanker.js";
import type { RedisClientLike } from "./redisClient.js";
import {
  sessionBrowserStatusKey,
  sessionCurrentScreenKey,
  sessionSafeActionsKey,
} from "./redisKeys.js";

export class LiveStateWriter {
  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly redis: RedisClientLike,
  ) {}

  async setCurrentScreen(
    session: BrowserSessionRecord,
    screen: ScreenState,
    screenshotArtifactId: string | null,
  ): Promise<void> {
    const extendedScreen = screen as ScreenState & { auth_state?: unknown };
    await this.redis.set(
      sessionCurrentScreenKey(this.config.redisKeyPrefix, session.demoSessionId),
      JSON.stringify({
        screen_id: screen.screen_id,
        browser_session_id: session.browserSessionId,
        url: screen.url,
        title: screen.title,
        summary: screen.summary.summary,
        screen_hash: screen.screen_hash,
        confidence: screen.confidence,
        screenshot_uri: screen.screenshot_uri,
        screenshot_artifact_id: screenshotArtifactId,
        auth_state: extendedScreen.auth_state ?? null,
        updated_at: new Date().toISOString(),
      }),
      "EX",
      this.config.redisSessionTtlSeconds,
    );
  }

  async setSafeActions(session: BrowserSessionRecord, safeActions: SafeActionInternal[]): Promise<void> {
    await this.redis.set(
      sessionSafeActionsKey(this.config.redisKeyPrefix, session.demoSessionId),
      JSON.stringify(safeActions),
      "EX",
      this.config.redisSessionTtlSeconds,
    );
  }

  async setBrowserStatus(session: BrowserSessionRecord): Promise<void> {
    await this.redis.set(
      sessionBrowserStatusKey(this.config.redisKeyPrefix, session.demoSessionId),
      JSON.stringify({
        browser_session_id: session.browserSessionId,
        status: session.status,
        current_url: session.page.url(),
        current_screen_id: session.currentScreenState?.screen_id ?? null,
        last_action_id: null,
        updated_at: new Date().toISOString(),
      }),
      "EX",
      this.config.redisSessionTtlSeconds,
    );
  }
}
