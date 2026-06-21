import type { BoundingBox } from "@live-demo-agent/contracts";

export type Size = { width: number; height: number };
export type Point = { x: number; y: number };
export type RenderedBox = { left: number; top: number; width: number; height: number };

export function mapPointContain(point: Point, source: Size, display: Size): Point {
  const transform = containTransform(source, display);
  return {
    x: transform.offsetX + point.x * transform.scale,
    y: transform.offsetY + point.y * transform.scale,
  };
}

export function mapBoundingBoxContain(bbox: BoundingBox, source: Size, display: Size): RenderedBox {
  const transform = containTransform(source, display);
  return {
    left: transform.offsetX + bbox.x * transform.scale,
    top: transform.offsetY + bbox.y * transform.scale,
    width: bbox.width * transform.scale,
    height: bbox.height * transform.scale,
  };
}

function containTransform(source: Size, display: Size): { scale: number; offsetX: number; offsetY: number } {
  if (source.width <= 0 || source.height <= 0 || display.width <= 0 || display.height <= 0) {
    return { scale: 0, offsetX: 0, offsetY: 0 };
  }
  const scale = Math.min(display.width / source.width, display.height / source.height);
  return {
    scale,
    offsetX: (display.width - source.width * scale) / 2,
    offsetY: (display.height - source.height * scale) / 2,
  };
}
