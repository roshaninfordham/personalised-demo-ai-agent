"use client";

import { memo, useEffect, useState } from "react";

import type { BrowserFrameMode, BrowserFrameState } from "../../lib/browser-view/frameStore";
import { EmptyState } from "./EmptyState";

export const BrowserFrame = memo(function BrowserFrame({
  frame,
  mode,
}: {
  frame: BrowserFrameState | null;
  mode: BrowserFrameMode;
}) {
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    setLoadError(false);
    if (frame?.imageUrl === null || frame?.imageUrl === undefined) return;
    const image = new Image();
    image.src = frame.imageUrl;
  }, [frame?.imageUrl]);

  if (mode !== "screenshot") {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title={`${mode} mode is not implemented in Phase 6.`} />
      </div>
    );
  }

  if (frame === null || frame.imageUrl === null) {
    return (
      <div className="browser-frame browser-frame-empty">
        <EmptyState title="Opening the product...">
          The agent is creating an isolated browser, loading the URL, and reading the first screen.
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
        src={frame.imageUrl}
        alt={frame.title === undefined ? "Controlled browser screenshot" : `Controlled browser: ${frame.title}`}
        onError={() => {
          setLoadError(true);
        }}
      />
    </div>
  );
});
