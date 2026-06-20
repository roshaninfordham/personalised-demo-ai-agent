import { describe, expect, it } from "vitest";

import { createInitialSessionState } from "../lib/sessionStore";

describe("createInitialSessionState", () => {
  it("returns a created demo session", () => {
    const session = createInitialSessionState("session_test");

    expect(session.session_id).toBe("session_test");
    expect(session.status).toBe("created");
  });
});
