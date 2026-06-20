import type { BrowserActionCommand, BrowserActionResult } from "@live-demo-agent/contracts";

import type { BrowserSessionRecord } from "../browser/browserSession.js";
import type { ScreenReader } from "../screen/screenReader.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import { diffScreens } from "../screen/screenDiffer.js";

export async function observeActionResult(
  session: BrowserSessionRecord,
  command: BrowserActionCommand,
  screenReader: ScreenReader,
  events: BrowserEventPublisher,
  startedAt: number,
  expectedNoScreenChange: boolean,
): Promise<BrowserActionResult> {
  const before = session.currentScreenState;
  const after = await screenReader.readCurrentScreen(session, { captureScreenshot: true });
  const diff = diffScreens(before, after);
  const success =
    expectedNoScreenChange || diff.urlChanged || diff.hashChanged || diff.elementJaccardDistance >= 0.15;
  const result: BrowserActionResult = {
    command_id: command.command_id,
    session_id: command.session_id,
    success,
    policy_decision: "allowed",
    risk_level: "low",
    latency_ms: Math.round(performance.now() - startedAt),
    created_at: new Date().toISOString(),
    new_screen_summary: after.summary.summary,
  };
  await events.publish(session, success ? "browser.action.completed" : "browser.action.failed", {
    command_id: command.command_id,
    success,
    diff,
  });
  await events.publish(session, "browser.screen.updated", {
    screen_id: after.screen_id,
    screen_hash: after.screen_hash,
  });
  return result;
}

