"use client";

import { useEffect, useState } from "react";

import { applyTheme, persistTheme, readStoredTheme, type ThemePreference } from "../../lib/theme/themeStore";

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemePreference>("light");

  useEffect(() => {
    const stored = readStoredTheme();
    setTheme(stored);
    applyTheme(stored);
  }, []);

  function toggle(): void {
    const next = theme === "light" ? "dark" : "light";
    setTheme(next);
    persistTheme(next);
    applyTheme(next);
  }

  return (
    <button type="button" className="theme-toggle" onClick={toggle} aria-label="Toggle color theme">
      {theme === "light" ? "Dark" : "Light"}
    </button>
  );
}
