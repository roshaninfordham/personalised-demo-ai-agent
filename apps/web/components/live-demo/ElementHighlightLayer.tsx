import type { ElementHighlightState } from "../../lib/events/eventTypes";
import { mapBoundingBoxContain, type Size } from "../../lib/browser-view/viewportMath";

export function ElementHighlightLayer({
  highlights,
  sourceSize,
  displaySize,
}: {
  highlights: ElementHighlightState[];
  sourceSize: Size;
  displaySize: Size;
}) {
  return (
    <div className="frame-overlay" aria-hidden="true">
      {highlights.map((highlight) => {
        const box = mapBoundingBoxContain(highlight.bbox, sourceSize, displaySize);
        return (
          <div
            key={highlight.elementId}
            className="highlight-box"
            style={{
              transform: `translate3d(${String(box.left)}px, ${String(box.top)}px, 0)`,
              width: box.width,
              height: box.height,
            }}
          >
            {highlight.label === undefined ? null : <span className="highlight-label">{highlight.label}</span>}
          </div>
        );
      })}
    </div>
  );
}
