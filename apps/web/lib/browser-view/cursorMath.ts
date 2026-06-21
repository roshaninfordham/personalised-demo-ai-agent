import type { Point } from "./viewportMath";

export function easeOutCubic(t: number): number {
  const clamped = Math.max(0, Math.min(1, t));
  return 1 - (1 - clamped) ** 3;
}

export function quadraticBezier(p0: Point, control: Point, p1: Point, t: number): Point {
  const clamped = Math.max(0, Math.min(1, t));
  const inverse = 1 - clamped;
  return {
    x: inverse ** 2 * p0.x + 2 * inverse * clamped * control.x + clamped ** 2 * p1.x,
    y: inverse ** 2 * p0.y + 2 * inverse * clamped * control.y + clamped ** 2 * p1.y,
  };
}

export function computeCursorDuration(
  distance: number,
  viewportDiagonal: number,
  minMs: number,
  maxMs: number,
): number {
  if (viewportDiagonal <= 0) return minMs;
  const normalized = Math.max(0, Math.min(1, distance / viewportDiagonal));
  return Math.round(minMs + normalized * (maxMs - minMs));
}
