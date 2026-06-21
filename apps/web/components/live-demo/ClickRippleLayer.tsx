import type { ClickRippleState } from "../../lib/events/eventTypes";
import { mapPointContain, type Size } from "../../lib/browser-view/viewportMath";

export function ClickRippleLayer({
  ripples,
  sourceSize,
  displaySize,
}: {
  ripples: ClickRippleState[];
  sourceSize: Size;
  displaySize: Size;
}) {
  return (
    <div className="frame-overlay" aria-hidden="true">
      {ripples.map((ripple) => {
        const point = mapPointContain({ x: ripple.x, y: ripple.y }, sourceSize, displaySize);
        return <span key={ripple.id} className="ripple" style={{ left: point.x, top: point.y }} />;
      })}
    </div>
  );
}
