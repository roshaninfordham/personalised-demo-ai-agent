"use client";

import { useEffect, useRef } from "react";

import { easeOutCubic, quadraticBezier } from "../../lib/browser-view/cursorMath";
import { mapPointContain, type Size } from "../../lib/browser-view/viewportMath";
import type { CursorState } from "../../lib/events/eventTypes";

export function CursorOverlay({
  cursor,
  sourceSize,
  displaySize,
}: {
  cursor: CursorState;
  sourceSize: Size;
  displaySize: Size;
}) {
  const cursorRef = useRef<HTMLSpanElement | null>(null);

  useEffect(() => {
    const node = cursorRef.current;
    if (node === null || !cursor.visible || cursor.target === null) return undefined;
    const source = cursor.source ?? cursor.target;
    const control = cursor.controlPoint ?? source;
    const target = cursor.target;
    let frame = 0;

    function animate(): void {
      const current = cursorRef.current;
      if (current === null) return;
      const elapsed = performance.now() - cursor.startedAtMs;
      const progress = cursor.durationMs <= 0 ? 1 : Math.min(1, elapsed / cursor.durationMs);
      const eased = cursor.easing === "linear" ? progress : easeOutCubic(progress);
      const browserPoint = quadraticBezier(source, control, target, eased);
      const renderPoint = mapPointContain(browserPoint, sourceSize, displaySize);
      current.style.transform = `translate3d(${String(renderPoint.x - 9)}px, ${String(renderPoint.y - 9)}px, 0)`;
      if (progress < 1) frame = requestAnimationFrame(animate);
    }

    frame = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(frame);
    };
  }, [cursor, displaySize, sourceSize]);

  return (
    <div className="frame-overlay" aria-hidden="true">
      <span ref={cursorRef} className="cursor-dot" />
    </div>
  );
}
