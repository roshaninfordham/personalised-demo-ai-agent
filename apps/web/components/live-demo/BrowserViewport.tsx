"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import type { BrowserFrameState } from "../../lib/browser-view/frameStore";
import { getPublicConfig } from "../../lib/config/publicConfig";
import type {
  ClickRippleState,
  CursorState,
  ElementHighlightState,
  EventConnectionStatus,
  ScrollIndicatorState,
} from "../../lib/events/eventTypes";
import type { Size } from "../../lib/browser-view/viewportMath";
import { Badge } from "../ui/Badge";
import { BrowserFrame } from "./BrowserFrame";
import { ClickRippleLayer } from "./ClickRippleLayer";
import { CursorOverlay } from "./CursorOverlay";
import { ElementHighlightLayer } from "./ElementHighlightLayer";
import { ScrollIndicatorLayer } from "./ScrollIndicatorLayer";

export type BrowserViewportProps = {
  frame: BrowserFrameState | null;
  cursor: CursorState;
  highlights: ElementHighlightState[];
  ripples: ClickRippleState[];
  scrollIndicators: ScrollIndicatorState[];
  connectionStatus: EventConnectionStatus;
};

export function BrowserViewport({
  frame,
  cursor,
  highlights,
  ripples,
  scrollIndicators,
  connectionStatus,
}: BrowserViewportProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [displaySize, setDisplaySize] = useState<Size>({ width: 0, height: 0 });
  const mode = getPublicConfig().browserFrameMode;
  const sourceSize = useMemo<Size>(
    () => ({ width: frame?.width ?? 1440, height: frame?.height ?? 900 }),
    [frame?.height, frame?.width],
  );

  useEffect(() => {
    const node = containerRef.current;
    if (node === null) return undefined;
    const update = (): void => {
      const rect = node.getBoundingClientRect();
      setDisplaySize({ width: rect.width, height: rect.height });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(node);
    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <section className="browser-stage">
      <div className="browser-stage-header">
        <div className="panel-title">
          <div>
            <h2>Product browser</h2>
            <span className="muted">{frame?.title ?? "Opening the product..."}</span>
          </div>
          <div className="row">
            <Badge tone={connectionStatus === "connected" ? "success" : "warning"}>
              {connectionStatus === "connected" ? "Live" : "Updating"}
            </Badge>
            <Badge>{mode}</Badge>
          </div>
        </div>
      </div>
      <div className="browser-stage-body">
        <div ref={containerRef} className="browser-viewport" data-testid="browser-viewport">
          <BrowserFrame frame={frame} mode={mode} />
          <ElementHighlightLayer highlights={highlights} sourceSize={sourceSize} displaySize={displaySize} />
          <ClickRippleLayer ripples={ripples} sourceSize={sourceSize} displaySize={displaySize} />
          <ScrollIndicatorLayer indicators={scrollIndicators} />
          <CursorOverlay cursor={cursor} sourceSize={sourceSize} displaySize={displaySize} />
          {frame?.stale === true ? (
            <span className="badge badge-warning stale-overlay">Frame stale</span>
          ) : null}
        </div>
        {frame?.url === undefined ? null : <span className="muted">{frame.url}</span>}
      </div>
    </section>
  );
}
