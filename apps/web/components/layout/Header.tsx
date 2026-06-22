import Link from "next/link";

import { ThemeToggle } from "../theme/ThemeToggle";
import { StatusBadge } from "./StatusBadge";

export function Header() {
  return (
    <header className="app-header">
      <div className="app-header-inner">
        <Link href="/" className="brand">
          <strong>Live Demo Agent</strong>
          <span>Realtime product demo room</span>
        </Link>
        <nav className="row" aria-label="Primary navigation">
          <Link href="/demo">Demo</Link>
          <Link href="/metrics">Metrics</Link>
          <Link href="/observability">Observability</Link>
          <Link href="/docs">Docs</Link>
          <StatusBadge status="Local Ready" tone="success" />
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
