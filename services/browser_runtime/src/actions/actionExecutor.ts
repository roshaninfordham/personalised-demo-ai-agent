import type { BrowserActionCommand, BrowserActionResult } from "@live-demo-agent/contracts";

import type { BrowserRuntimeConfig } from "../config.js";
import { BrowserRuntimeError } from "../errors.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import { goBack, navigateSession } from "../browser/navigation.js";
import { waitForPageIdle } from "../browser/waitStrategies.js";
import type { BrowserEventPublisher } from "../events/browserEventPublisher.js";
import type { CursorEventEmitter } from "../events/cursorEventEmitter.js";
import type { ScreenReader } from "../screen/screenReader.js";
import { recordBrowserAction } from "../observability/browserInstrumentation.js";
import { checkLatencyBudget } from "../observability/latencyBudget.js";
import { observeActionResult } from "./actionObservation.js";
import { validateAction } from "./actionValidator.js";

export class ActionExecutor {
  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly events: BrowserEventPublisher,
    private readonly cursor: CursorEventEmitter,
    private readonly screenReader: ScreenReader,
  ) {}

  async execute(session: BrowserSessionRecord, command: BrowserActionCommand): Promise<BrowserActionResult> {
    const started = performance.now();
    const validated = validateAction(session, command, this.config);
    if (validated.policyDecision === "confirmation_required") {
      const latencyMs = Math.round(performance.now() - started);
      recordBrowserAction(command.action_type, validated.riskLevel, "blocked", latencyMs);
      checkLatencyBudget("browser_action_total", latencyMs);
      return {
        command_id: command.command_id,
        session_id: command.session_id,
        success: false,
        policy_decision: "confirmation_required",
        risk_level: validated.riskLevel,
        latency_ms: Math.round(performance.now() - started),
        created_at: new Date().toISOString(),
        error_code: "confirmation_required",
        error_message: "High-risk action requires confirmation.",
      };
    }
    session.actionInFlight = true;
    let result: "success" | "failed" = "success";
    try {
      await this.events.publish(session, "browser.action.started", {
        command_id: command.command_id,
        action_type: command.action_type,
      });
      switch (command.action_type) {
        case "read_current_screen": {
          const screen = await this.screenReader.readCurrentScreen(session, { captureScreenshot: true });
          return {
            command_id: command.command_id,
            session_id: command.session_id,
            success: true,
            policy_decision: "allowed",
            risk_level: "low",
            latency_ms: Math.round(performance.now() - started),
            created_at: new Date().toISOString(),
            new_screen_summary: screen.summary.summary,
          };
        }
        case "highlight_element": {
          const element = requireElement(validated.resolvedElement);
          await this.cursor.emitHighlight(session, element.element.element_id);
          return await observeActionResult(session, command, this.screenReader, this.events, started, true);
        }
        case "click_element": {
          const element = requireElement(validated.resolvedElement);
          await this.cursor.emitMoveToElement(session, command.command_id, element.element.bbox);
          await this.cursor.emitHighlight(session, element.element.element_id);
          await this.cursor.emitClick(session, element.element.bbox);
          await element.locator.click({ timeout: this.config.browserActionTimeoutMs });
          await waitForPageIdle(session.page, this.config);
          return await observeActionResult(session, command, this.screenReader, this.events, started, false);
        }
        case "type_into_element": {
          const element = requireElement(validated.resolvedElement);
          await this.cursor.emitMoveToElement(session, command.command_id, element.element.bbox);
          await this.cursor.emitHighlight(session, element.element.element_id);
          await element.locator.fill(command.text ?? "", { timeout: this.config.browserActionTimeoutMs });
          await waitForPageIdle(session.page, this.config);
          return await observeActionResult(session, command, this.screenReader, this.events, started, false);
        }
        case "scroll": {
          const amount = command.direction === "up" || command.direction === "left" ? -700 : 700;
          if (command.direction === "left" || command.direction === "right") {
            await session.page.mouse.wheel(amount, 0);
          } else {
            await session.page.mouse.wheel(0, amount);
          }
          await waitForPageIdle(session.page, this.config);
          return await observeActionResult(session, command, this.screenReader, this.events, started, true);
        }
        case "go_back": {
          await goBack(session.page, this.config);
          return await observeActionResult(session, command, this.screenReader, this.events, started, false);
        }
        case "navigate_to_allowed_url": {
          if (!command.url) {
            throw new BrowserRuntimeError("missing_url", "Navigation requires a URL.", 422);
          }
          await navigateSession(session, command.url, this.config, this.events, this.screenReader);
          return await observeActionResult(session, command, this.screenReader, this.events, started, false);
        }
        case "wait_for_idle": {
          await waitForPageIdle(session.page, this.config);
          return await observeActionResult(session, command, this.screenReader, this.events, started, true);
        }
        default:
          throw new BrowserRuntimeError("unsupported_action", "Browser action is unsupported.", 422);
      }
    } catch (error) {
      result = "failed";
      throw error;
    } finally {
      const latencyMs = Math.round(performance.now() - started);
      recordBrowserAction(command.action_type, validated.riskLevel, result, latencyMs);
      checkLatencyBudget("browser_action_total", latencyMs);
      session.actionInFlight = false;
      session.lastActionAt = new Date().toISOString();
    }
  }
}

function requireElement<T>(value: T | undefined): T {
  if (value === undefined) {
    throw new BrowserRuntimeError("missing_resolved_element", "Action requires a resolved element.", 409);
  }
  return value;
}
