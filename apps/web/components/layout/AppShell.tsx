import type { ReactNode } from "react";

import { Footer } from "./Footer";
import { Header } from "./Header";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <Header />
      <div className="app-main">{children}</div>
      <Footer />
    </div>
  );
}
