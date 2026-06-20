type CursorOverlayProps = {
  x: number;
  y: number;
};

export function CursorOverlay({ x, y }: CursorOverlayProps) {
  return (
    <div
      aria-hidden="true"
      style={{
        background: "#111827",
        border: "2px solid #ffffff",
        borderRadius: "999px",
        height: 16,
        left: x,
        position: "absolute",
        top: y,
        width: 16,
      }}
    />
  );
}
