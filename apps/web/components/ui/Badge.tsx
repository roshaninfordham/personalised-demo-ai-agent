import type { ReactNode } from "react";

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  const toneClass = tone === "neutral" ? "" : ` badge-${tone}`;
  return <span className={`badge${toneClass}`}>{children}</span>;
}
