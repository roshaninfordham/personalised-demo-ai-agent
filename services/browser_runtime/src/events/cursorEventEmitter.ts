import { createHash } from "node:crypto";

import type { BoundingBox } from "@live-demo-agent/contracts";

import type { BrowserRuntimeConfig } from "../config.js";
import type { BrowserSessionRecord } from "../browser/browserSession.js";
import { bboxCenter } from "../screen/elementExtractor.js";
import type { BrowserEventPublisher } from "./browserEventPublisher.js";

export class CursorEventEmitter {
  constructor(
    private readonly config: BrowserRuntimeConfig,
    private readonly events: BrowserEventPublisher,
  ) {}

  async emitMoveToElement(
    session: BrowserSessionRecord,
    actionId: string,
    bbox: BoundingBox,
  ): Promise<void> {
    const target = bboxCenter(bbox);
    const path = computeCursorPath(
      session.cursorPosition,
      target,
      { width: this.config.browserViewportWidth, height: this.config.browserViewportHeight },
      this.config.cursorMoveMinDurationMs,
      this.config.cursorMoveMaxDurationMs,
      actionId,
    );
    await this.events.publish(session, "browser.cursor.move", {
      ...path,
      easing: this.config.cursorEasing,
    });
    session.cursorPosition = target;
  }

  async emitHighlight(session: BrowserSessionRecord, elementId: string): Promise<void> {
    await this.events.publish(session, "browser.element.highlight", {
      element_id: elementId,
      duration_ms: this.config.elementHighlightDurationMs,
    });
  }

  async emitClick(session: BrowserSessionRecord, bbox: BoundingBox): Promise<void> {
    const target = bboxCenter(bbox);
    await this.events.publish(session, "browser.cursor.click", {
      x: target.x,
      y: target.y,
    });
    if (this.config.cursorClickRippleEnabled) {
      await this.events.publish(session, "browser.cursor.ripple", {
        x: target.x,
        y: target.y,
      });
    }
  }
}

export function computeCursorPath(
  start: { x: number; y: number },
  target: { x: number; y: number },
  viewport: { width: number; height: number },
  minMs: number,
  maxMs: number,
  actionId: string,
): {
  start_x: number;
  start_y: number;
  x: number;
  y: number;
  duration_ms: number;
  control_x: number;
  control_y: number;
} {
  const dx = target.x - start.x;
  const dy = target.y - start.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  const maxDistance = Math.sqrt(viewport.width * viewport.width + viewport.height * viewport.height);
  const normalizedDistance = Math.max(0, Math.min(1, distance / maxDistance));
  const duration = Math.round(minMs + normalizedDistance * (maxMs - minMs));
  const midpoint = { x: (start.x + target.x) / 2, y: (start.y + target.y) / 2 };
  const sign = (createHash("sha256").update(actionId).digest()[0] ?? 0) % 2 === 0 ? 1 : -1;
  const offset = Math.min(80, 0.15 * distance) * sign;
  return {
    start_x: start.x,
    start_y: start.y,
    x: target.x,
    y: target.y,
    duration_ms: Math.max(minMs, Math.min(maxMs, duration)),
    control_x: midpoint.x - dy * 0.001 * offset,
    control_y: midpoint.y + dx * 0.001 * offset,
  };
}
