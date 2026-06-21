"use client";

import { useEffect, useState } from "react";

import { requestMicrophone, setStreamMuted, stopMediaStream } from "../lib/media/microphone";
import type { CallConnectionStatus } from "../lib/media/mediaTypes";

export function useMicrophone(): {
  status: CallConnectionStatus;
  stream: MediaStream | null;
  muted: boolean;
  error: string | null;
  request: () => Promise<void>;
  toggleMute: () => void;
} {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [status, setStatus] = useState<CallConnectionStatus>("idle");
  const [muted, setMuted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => {
    if (stream !== null) stopMediaStream(stream);
  }, [stream]);

  return {
    status,
    stream,
    muted,
    error,
    async request() {
      setStatus("requesting_microphone");
      setError(null);
      try {
        const next = await requestMicrophone();
        setStream(next);
        setStatus("microphone_ready");
      } catch (err: unknown) {
        const message = err instanceof DOMException ? micErrorMessage(err.name) : "Microphone permission failed.";
        setStatus("failed");
        setError(message);
      }
    },
    toggleMute() {
      if (stream === null) return;
      const next = !muted;
      setStreamMuted(stream, next);
      setMuted(next);
      setStatus(next ? "muted" : "microphone_ready");
    },
  };
}

function micErrorMessage(name: string): string {
  if (name === "NotAllowedError") return "Microphone permission was denied.";
  if (name === "NotFoundError") return "No microphone was found.";
  if (name === "NotReadableError") return "Microphone is already in use.";
  return "Microphone permission failed.";
}
