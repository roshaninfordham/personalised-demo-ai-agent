"use client";

export type ThemePreference = "light" | "dark";

const storageKey = "live-demo-agent-theme";

export function readStoredTheme(): ThemePreference {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem(storageKey);
  return stored === "dark" ? "dark" : "light";
}

export function applyTheme(theme: ThemePreference): void {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
}

export function persistTheme(theme: ThemePreference): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(storageKey, theme);
}
