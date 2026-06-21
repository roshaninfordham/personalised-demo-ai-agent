import type { ReactNode } from "react";

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      {children === undefined ? null : <div style={{ marginTop: 6 }}>{children}</div>}
    </div>
  );
}
