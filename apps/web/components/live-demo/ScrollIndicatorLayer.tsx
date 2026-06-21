import type { ScrollIndicatorState } from "../../lib/events/eventTypes";

export function ScrollIndicatorLayer({ indicators }: { indicators: ScrollIndicatorState[] }) {
  return (
    <div className="frame-overlay" aria-hidden="true">
      {indicators.map((indicator) => (
        <span
          key={indicator.id}
          className="badge stale-overlay"
          style={{ top: 48 }}
        >
          Scroll {indicator.direction}
        </span>
      ))}
    </div>
  );
}
