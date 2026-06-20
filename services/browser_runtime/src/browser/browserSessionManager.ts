import { randomUUID } from "node:crypto";

import type { BrowserRuntimeConfig } from "../config.js";
import { BrowserRuntimeError, notFound } from "../errors.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import type { LiveStateWriter } from "../redis/liveStateWriter.js";
import { validateNavigationUrl } from "./navigation.js";
import { installPageGuards } from "./pageGuards.js";
import type { PlaywrightFactory } from "./playwrightFactory.js";
import type { BrowserSessionRecord, CreateBrowserSessionInput } from "./browserSession.js";

export class BrowserSessionManager {
  private readonly sessions = new Map<string, BrowserSessionRecord>();
  private cleanupTimer: NodeJS.Timeout | undefined;

  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly playwrightFactory: PlaywrightFactory,
    private readonly events: BrowserEventPublisher,
    private readonly liveState: LiveStateWriter,
  ) {}

  activeCount(): number {
    return this.sessions.size;
  }

  getSession(browserSessionId: string): BrowserSessionRecord {
    const session = this.sessions.get(browserSessionId);
    if (session === undefined) {
      throw notFound();
    }
    return session;
  }

  async createSession(input: CreateBrowserSessionInput): Promise<BrowserSessionRecord> {
    if (this.sessions.size >= this.config.browserMaxConcurrentSessions) {
      throw new BrowserRuntimeError(
        "browser_session_limit_reached",
        "Browser session limit reached.",
        429,
      );
    }
    if (input.startUrl !== undefined) {
      const validation = validateNavigationUrl(input.startUrl, {
        appEnv: this.config.appEnv,
        allowLocalProductUrls: this.config.allowLocalProductUrls,
        allowedDomains: input.allowedDomains,
        blockExternalNavigation: this.config.browserBlockExternalNavigation,
        maxUrlLength: 2048,
      });
      if (!validation.ok) {
        throw new BrowserRuntimeError(validation.errorCode, validation.message, 422);
      }
    }
    const browser = await this.playwrightFactory.getBrowser();
    const context = await browser.newContext({
      viewport: input.viewport,
      acceptDownloads: this.config.allowDownloads,
    });
    const page = await context.newPage();
    const browserSessionId = randomUUID();
    const now = new Date();
    const expires = new Date(now.getTime() + this.config.browserSessionTtlSeconds * 1000);
    const session: BrowserSessionRecord = {
      browserSessionId,
      organizationId: input.organizationId,
      demoSessionId: input.demoSessionId,
      productId: input.productId,
      allowedDomains: input.allowedDomains,
      status: "ready",
      createdAt: now.toISOString(),
      updatedAt: now.toISOString(),
      expiresAt: expires.toISOString(),
      context,
      page,
      currentElements: new Map(),
      currentSafeActions: [],
      actionInFlight: false,
      cursorPosition: { x: 0, y: 0 },
      screenIdsByHash: new Map(),
    };
    await installPageGuards(page, session, this.config, this.events);
    this.sessions.set(browserSessionId, session);
    await this.liveState.setBrowserStatus(session);
    await this.events.publish(session, "browser.session.created", {
      browser_session_id: browserSessionId,
    });
    return session;
  }

  async closeSession(browserSessionId: string): Promise<void> {
    const session = this.sessions.get(browserSessionId);
    if (session === undefined) {
      return;
    }
    session.status = "closing";
    await session.page.close().catch(() => undefined);
    await session.context.close().catch(() => undefined);
    session.status = "closed";
    this.sessions.delete(browserSessionId);
    await this.liveState.setBrowserStatus(session);
    await this.events.publish(session, "browser.session.closed", {
      browser_session_id: browserSessionId,
    });
  }

  async closeExpiredSessions(): Promise<number> {
    const now = Date.now();
    let closed = 0;
    for (const session of this.sessions.values()) {
      if (Date.parse(session.expiresAt) <= now) {
        await this.closeSession(session.browserSessionId);
        closed += 1;
      }
    }
    return closed;
  }

  startCleanupLoop(): void {
    this.cleanupTimer = setInterval(() => {
      void this.closeExpiredSessions();
    }, this.config.browserCleanupIntervalMs);
    this.cleanupTimer.unref();
  }

  async shutdown(): Promise<void> {
    if (this.cleanupTimer !== undefined) {
      clearInterval(this.cleanupTimer);
    }
    await Promise.all([...this.sessions.keys()].map((id) => this.closeSession(id)));
    await this.playwrightFactory.close();
  }
}
