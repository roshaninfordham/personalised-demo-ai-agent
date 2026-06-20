import { Redis } from "ioredis";

import type { BrowserRuntimeConfig } from "../config.js";

export type RedisClientLike = {
  ping(): Promise<string>;
  get(key: string): Promise<string | null>;
  set(key: string, value: string, mode?: "EX", ttlSeconds?: number): Promise<string | null>;
  del(key: string): Promise<number>;
  xadd(key: string, ...args: Array<string | number>): Promise<string>;
  quit(): Promise<unknown>;
};

export function createRedisClient(config: BrowserRuntimeConfig): RedisClientLike {
  const client = new Redis(config.redisUrl, {
    lazyConnect: false,
    maxRetriesPerRequest: 1,
  });
  return {
    ping: () => client.ping(),
    get: (key: string) => client.get(key),
    set: (key: string, value: string, mode?: "EX", ttlSeconds?: number) => {
      if (mode === "EX" && ttlSeconds !== undefined) {
        return client.set(key, value, "EX", ttlSeconds);
      }
      return client.set(key, value);
    },
    del: (key: string) => client.del(key),
    xadd: async (key: string, ...args: Array<string | number>) =>
      (await client.xadd(key, ...args)) ?? "0-0",
    quit: () => client.quit(),
  };
}

export class InMemoryRedisClient implements RedisClientLike {
  private readonly values = new Map<string, string>();
  readonly streams = new Map<string, Array<Record<string, string | number>>>();

  ping(): Promise<string> {
    return Promise.resolve("PONG");
  }

  get(key: string): Promise<string | null> {
    return Promise.resolve(this.values.get(key) ?? null);
  }

  set(key: string, value: string): Promise<string> {
    this.values.set(key, value);
    return Promise.resolve("OK");
  }

  del(key: string): Promise<number> {
    return Promise.resolve(this.values.delete(key) ? 1 : 0);
  }

  xadd(key: string, ...args: Array<string | number>): Promise<string> {
    const stream = this.streams.get(key) ?? [];
    const record: Record<string, string | number> = {};
    for (let index = 0; index < args.length - 1; index += 2) {
      const value = args[index + 1];
      if (value !== undefined) {
        record[String(args[index])] = value;
      }
    }
    stream.push(record);
    this.streams.set(key, stream);
    return Promise.resolve(`${String(Date.now())}-0`);
  }

  quit(): Promise<void> {
    return Promise.resolve(undefined);
  }
}
