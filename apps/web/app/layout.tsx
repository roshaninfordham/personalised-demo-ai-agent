import type { Metadata } from "next";
import Script from "next/script";
import type { ReactNode } from "react";

import "./design-tokens.css";
import "./globals.css";
import { AppShell } from "../components/layout/AppShell";

export const metadata: Metadata = {
  title: "Live Demo Agent",
  description: "Frontend shell for live AI product-demo sessions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script src="/runtime-config.js" strategy="beforeInteractive" />
      </head>
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
