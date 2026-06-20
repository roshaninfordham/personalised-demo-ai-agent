import { randomUUID } from "node:crypto";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import type { RedisClientLike } from "../redis/redisClient.js";
import { globalEventsStreamKey, sessionEventsStreamKey } from "../redis/redisKeys.js";
import type { BrowserEventType } from "./eventTypes.js";

export class BrowserEventPublisher {
  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly redis: RedisClientLike,
  ) {}

  async publish(
    session: BrowserSessionRecord,
    eventType: BrowserEventType,
    payload: Record<string, unknown>,
  ): Promise<void> {
    const traceId = typeof payload.trace_id === "string" ? payload.trace_id : session.demoSessionId;
    const event = {
      event_id: randomUUID(),
      session_id: session.demoSessionId,
      browser_session_id: session.browserSessionId,
      organization_id: session.organizationId,
      event_type: eventType,
      created_at: new Date().toISOString(),
      trace_id: traceId,
      payload,
    };
    const fields = {
      event_json: JSON.stringify(event),
      event_type: eventType,
      trace_id: event.trace_id,
    };
    await this.redis.xadd(
      sessionEventsStreamKey(this.config.redisKeyPrefix, session.demoSessionId),
      "MAXLEN",
      "~",
      this.config.redisEventStreamMaxLen,
      "*",
      ...Object.entries(fields).flat(),
    );
    await this.redis.xadd(
      globalEventsStreamKey(this.config.redisKeyPrefix),
      "MAXLEN",
      "~",
      this.config.redisEventStreamMaxLen,
      "*",
      ...Object.entries(fields).flat(),
    );
  }
}

export class NoopBrowserEventPublisher extends BrowserEventPublisher {
  constructor(config: BrowserRuntimeConfig) {
    super(config, {
      ping: () => Promise.resolve("PONG"),
      get: () => Promise.resolve(null),
      set: () => Promise.resolve("OK"),
      del: () => Promise.resolve(1),
      xadd: () => Promise.resolve("0-0"),
      quit: () => Promise.resolve(undefined),
    });
  }
}
