import type { Page } from "playwright";

export async function extractVisibleText(page: Page, maxChars: number): Promise<string> {
  const text = await page.locator("body").innerText({ timeout: 1_000 }).catch(() => "");
  return normalizeVisibleText(text).slice(0, maxChars);
}

export function normalizeVisibleText(text: string): string {
  return text.replace(/\r/g, "\n").replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
}

