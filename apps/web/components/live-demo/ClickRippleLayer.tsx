import { useEffect, useState } from "react";

import type { ClickRippleState } from "../../lib/events/eventTypes";
import { mapPointContain, type Size } from "../../lib/browser-view/viewportMath";

const RIPPLE_VISIBLE_MS = 1_800;

export function ClickRippleLayer({
  ripples,
  sourceSize,
  displaySize,
}: {
  ripples: ClickRippleState[];
  sourceSize: Size;
  displaySize: Size;
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (ripples.length === 0) return undefined;
    const timer = window.setInterval(() => {
      setNow(Date.now());
    }, 250);
    return () => {
      window.clearInterval(timer);
    };
  }, [ripples.length]);

  const visibleRipples = ripples.filter((ripple) => now - ripple.startedAtMs <= RIPPLE_VISIBLE_MS);

  return (
    <div className="frame-overlay" aria-hidden="true">
      {visibleRipples.map((ripple) => {
        const point = mapPointContain({ x: ripple.x, y: ripple.y }, sourceSize, displaySize);
        return (
          <span
            key={ripple.id}
            className="ripple"
            data-testid="click-ripple"
            style={{ left: point.x, top: point.y }}
          />
        );
      })}
    </div>
  );
}
