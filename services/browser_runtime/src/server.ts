import Fastify, { type FastifyInstance } from "fastify";

import { getConfig, safeConfig, type BrowserRuntimeConfig } from "./config.js";
import { BrowserRuntimeError, errorEnvelope } from "./errors.js";
import { Logger, logContext } from "./logger.js";
import { contextFromRequest } from "./requestContext.js";
import { ActionExecutor } from "./actions/actionExecutor.js";
import { PlaywrightFactory } from "./browser/playwrightFactory.js";
import { BrowserSessionManager } from "./browser/browserSessionManager.js";
import { CursorEventEmitter } from "./events/cursorEventEmitter.js";
import { BrowserEventPublisher } from "./events/browserEventPublisher.js";
import { createRedisClient, type RedisClientLike } from "./redis/redisClient.js";
import { LiveStateWriter } from "./redis/liveStateWriter.js";
import { ScreenReader } from "./screen/screenReader.js";
import { S3ArtifactStore } from "./storage/s3ArtifactStore.js";
import type { ArtifactStore } from "./storage/artifactStore.js";
import { registerHealthRoutes } from "./routes/healthRoutes.js";
import { registerBrowserSessionRoutes } from "./routes/browserSessionRoutes.js";
import { registerNavigationRoutes } from "./routes/navigationRoutes.js";
import { registerScreenRoutes } from "./routes/screenRoutes.js";
import { registerActionRoutes } from "./routes/actionRoutes.js";
import { browserMetrics } from "./observability/metrics.js";
import { setupObservabilityRoutes } from "./observability/setup.js";

export type BrowserRuntimeDependencies = {
  config: BrowserRuntimeConfig;
  logger: Logger;
  redis: RedisClientLike;
  artifactStore: ArtifactStore;
  playwrightFactory: PlaywrightFactory;
  events: BrowserEventPublisher;
  liveState: LiveStateWriter;
  screenReader: ScreenReader;
  sessionManager: BrowserSessionManager;
  actionExecutor: ActionExecutor;
};

export function buildDependencies(config = getConfig()): BrowserRuntimeDependencies {
  const logger = new Logger(config.logLevel === "debug" ? "debug" : "info");
  const redis = createRedisClient(config);
  const artifactStore = new S3ArtifactStore(config);
  const playwrightFactory = new PlaywrightFactory(config);
  const events = new BrowserEventPublisher(config, redis);
  const liveState = new LiveStateWriter(config, redis);
  const screenReader = new ScreenReader(config, artifactStore, liveState);
  const cursor = new CursorEventEmitter(config, events);
  const sessionManager = new BrowserSessionManager(config, playwrightFactory, events, liveState);
  const actionExecutor = new ActionExecutor(config, events, cursor, screenReader);
  return {
    config,
    logger,
    redis,
    artifactStore,
    playwrightFactory,
    events,
    liveState,
    screenReader,
    sessionManager,
    actionExecutor,
  };
}

export function buildServer(deps = buildDependencies()): FastifyInstance {
  const server = Fastify({ logger: false });

  server.addHook("onRequest", (request, reply, done) => {
    const context = contextFromRequest(request);
    void reply.header("x-request-id", context.requestId);
    void reply.header("x-trace-id", context.traceId);
    logContext.run({ requestId: context.requestId, traceId: context.traceId }, done);
  });

  server.addHook("onResponse", (request, reply, done) => {
    browserMetrics.increment("live_demo_events_published_total", {
      event_type_group: "http",
      result: reply.statusCode >= 500 ? "failed" : "success",
    });
    deps.logger.info("http.request.completed", {
      method: request.method,
      path: request.url,
      status_code: reply.statusCode,
    });
    done();
  });

  server.setErrorHandler((error, request, reply) => {
    const context = contextFromRequest(request);
    const message = error instanceof Error ? error.message : "Unknown error";
    const runtimeError =
      error instanceof BrowserRuntimeError
        ? error
        : new BrowserRuntimeError("internal_error", "Internal browser runtime error.", 500);
    deps.logger.error("browser-runtime.error", {
      code: runtimeError.code,
      message,
    });
    void reply
      .status(runtimeError.statusCode)
      .send(errorEnvelope(runtimeError, context.requestId, context.traceId));
  });

  registerHealthRoutes(server, deps);
  registerBrowserSessionRoutes(server, deps);
  registerNavigationRoutes(server, deps);
  registerScreenRoutes(server, deps);
  registerActionRoutes(server, deps);
  setupObservabilityRoutes(server);

  server.addHook("onClose", async () => {
    await deps.sessionManager.shutdown();
    await deps.redis.quit();
  });

  deps.logger.info("browser-runtime.config.loaded", { config: safeConfig(deps.config) });
  deps.sessionManager.startCleanupLoop();
  return server;
}

export async function startServer(): Promise<void> {
  const deps = buildDependencies();
  const server = buildServer(deps);
  await server.listen({ host: deps.config.host, port: deps.config.port });
  deps.logger.info("browser-runtime.started", {
    host: deps.config.host,
    port: deps.config.port,
  });
}
