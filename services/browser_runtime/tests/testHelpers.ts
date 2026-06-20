import { createServer, type Server } from "node:http";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { getConfig, type BrowserRuntimeConfig } from "../src/config.js";
import { InMemoryArtifactStore } from "../src/storage/artifactStore.js";
import { InMemoryRedisClient } from "../src/redis/redisClient.js";
import { LiveStateWriter } from "../src/redis/liveStateWriter.js";
import { NoopBrowserEventPublisher } from "../src/events/browserEventPublisher.js";
import { PlaywrightFactory } from "../src/browser/playwrightFactory.js";
import { BrowserSessionManager } from "../src/browser/browserSessionManager.js";
import { ScreenReader } from "../src/screen/screenReader.js";
import { CursorEventEmitter } from "../src/events/cursorEventEmitter.js";
import { ActionExecutor } from "../src/actions/actionExecutor.js";

export type TestRuntime = {
  config: BrowserRuntimeConfig;
  redis: InMemoryRedisClient;
  artifactStore: InMemoryArtifactStore;
  events: NoopBrowserEventPublisher;
  playwrightFactory: PlaywrightFactory;
  liveState: LiveStateWriter;
  screenReader: ScreenReader;
  sessionManager: BrowserSessionManager;
  actionExecutor: ActionExecutor;
  shutdown(): Promise<void>;
};

export function buildTestRuntime(): TestRuntime {
  const config = getConfig({
    APP_ENV: "local",
    ALLOW_LOCAL_PRODUCT_URLS: "true",
    BROWSER_HEADLESS: "true",
    BROWSER_ENABLE_SCREENSHOTS: "true",
    BROWSER_MAX_CONCURRENT_SESSIONS: "3",
    BROWSER_BLOCK_EXTERNAL_NAVIGATION: "true",
    OBJECT_STORAGE_SECRET_KEY: "test",
  });
  const redis = new InMemoryRedisClient();
  const artifactStore = new InMemoryArtifactStore();
  const events = new NoopBrowserEventPublisher(config);
  const playwrightFactory = new PlaywrightFactory(config);
  const liveState = new LiveStateWriter(config, redis);
  const screenReader = new ScreenReader(config, artifactStore, liveState);
  const cursor = new CursorEventEmitter(config, events);
  const sessionManager = new BrowserSessionManager(config, playwrightFactory, events, liveState);
  const actionExecutor = new ActionExecutor(config, events, cursor, screenReader);
  return {
    config,
    redis,
    artifactStore,
    events,
    playwrightFactory,
    liveState,
    screenReader,
    sessionManager,
    actionExecutor,
    async shutdown() {
      await sessionManager.shutdown();
    },
  };
}

export async function startFixtureServer(): Promise<{ server: Server; origin: string; close(): Promise<void> }> {
  const server = createServer((request, response) => {
    void (async () => {
      const path = request.url?.split("?")[0] ?? "/";
      const fileName = path === "/" ? "simple-dashboard.html" : path.replace(/^\//, "");
      if (path === "/redirect-external") {
        response.writeHead(302, { location: "https://evil.example.net" });
        response.end();
        return;
      }
      try {
        const html = await readFile(join(process.cwd(), "tests/fixtures", fileName), "utf8");
        response.writeHead(200, { "content-type": "text/html" });
        response.end(html);
      } catch {
        response.writeHead(404, { "content-type": "text/plain" });
        response.end("not found");
      }
    })();
  });
  await new Promise<void>((resolve) => {
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  if (address === null || typeof address === "string") {
    throw new Error("Fixture server did not bind to a TCP port.");
  }
  return {
    server,
    origin: `http://127.0.0.1:${String(address.port)}`,
    close: async () => {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
          } else {
            resolve();
          }
        });
      });
    },
  };
}

export async function createTestSession(runtime: TestRuntime, origin: string) {
  return runtime.sessionManager.createSession({
    organizationId: "00000000-0000-0000-0000-000000000001",
    demoSessionId: "00000000-0000-0000-0000-000000000010",
    productId: "00000000-0000-0000-0000-000000000020",
    viewport: { width: 1280, height: 800 },
    allowedDomains: ["127.0.0.1"],
    startUrl: origin,
  });
}
