import { describe, expect, it } from "vitest";

import { InMemoryArtifactStore } from "../src/storage/artifactStore.js";
import { screenshotObjectKey } from "../src/storage/objectKeys.js";

describe("artifact store", () => {
  it("validates screenshot object keys and hashes bytes", async () => {
    const key = screenshotObjectKey({
      organizationId: "00000000-0000-0000-0000-000000000001",
      demoSessionId: "00000000-0000-0000-0000-000000000010",
      browserSessionId: "00000000-0000-0000-0000-000000000100",
      screenId: "screen_abc",
      extension: "webp",
    });
    expect(key).toContain("/screenshots/screen_abc.webp");
    const store = new InMemoryArtifactStore();
    const artifact = await store.putObject({
      artifactId: "artifact",
      objectKey: key,
      content: new Uint8Array([1, 2, 3]),
      contentType: "image/webp",
      metadata: {},
    });
    expect(artifact.sha256Hex).toHaveLength(64);
  });
});

