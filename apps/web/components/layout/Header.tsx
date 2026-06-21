import Link from "next/link";

import { StatusBadge } from "./StatusBadge";

export function Header() {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <Link href="/" className="brand">
          <strong>Live Demo Agent</strong>
          <span>Frontend live demo shell</span>
        </Link>
        <nav className="row" aria-label="Primary navigation">
          <Link href="/demo">Demo</Link>
          <StatusBadge status="Phase 6" tone="warning" />
        </nav>
      </div>
    </header>
  );
}
