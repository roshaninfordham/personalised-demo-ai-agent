"use client";

import { memo, useEffect, useState } from "react";

import type { BrowserFrameMode, BrowserFrameState } from "../../lib/browser-view/frameStore";
import { getPublicConfig } from "../../lib/config/publicConfig";
import { EmptyState } from "./EmptyState";

export const BrowserFrame = memo(function BrowserFrame({
  frame,
  mode,
}: {
  frame: BrowserFrameState | null;
  mode: BrowserFrameMode;
}) {
  const [loadError, setLoadError] = useState(false);
  const config = getPublicConfig();
  const imageUrl = resolveFrameUrl(frame?.imageUrl ?? null, config.apiBaseUrl);
  const blockedMockFrame =
    imageUrl !== null && imageUrl.startsWith("data:image/svg") && !config.enableMockDemo;

  useEffect(() => {
    setLoadError(false);
    if (imageUrl === null || blockedMockFrame) return;
    const image = new Image();
    image.src = imageUrl;
  }, [blockedMockFrame, imageUrl]);

  if (mode !== "screenshot") {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title={`${mode} mode is not available in this local run.`}>
          The demo is using screenshot frames from the controlled Playwright browser.
        </EmptyState>
      </div>
    );
  }

  if (frame === null || imageUrl === null) {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title="Opening the product...">
          The agent is creating an isolated browser, loading the URL, and reading the first screen.
        </EmptyState>
      </div>
    );
  }

  if (blockedMockFrame) {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title="Mock browser frame blocked">
          Real URL demos must render a Playwright screenshot. Enable fixture demo mode only for CI or
          local mock tests.
        </EmptyState>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title="We could not show the browser frame">
          Try refreshing the session or use the sample URL from the homepage.
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="browser-frame">
      <img
        src={imageUrl}
        alt={frame.title === undefined ? "Controlled browser screenshot" : `Controlled browser: ${frame.title}`}
        onError={() => {
          setLoadError(true);
        }}
      />
    </div>
  );
});

function resolveFrameUrl(value: string | null, apiBaseUrl: string): string | null {
  if (value === null || value.trim() === "") return null;
  if (value.startsWith("/api/")) {
    return `${apiBaseUrl.replace(/\/$/u, "")}${value}`;
  }
  return value;
}
