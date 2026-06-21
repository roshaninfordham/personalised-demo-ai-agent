"use client";

import { useEffect, useMemo, useState } from "react";

import { useMicrophone } from "../../hooks/useMicrophone";
import type { TranscriptItem } from "../../lib/events/eventTypes";
import type { CallConnectionStatus } from "../../lib/media/mediaTypes";
import { createPlaceholderRealtimeCallClient } from "../../lib/media/webrtcClient";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { AgentAudioPanel } from "./AgentAudioPanel";
import { ErrorBanner } from "./ErrorBanner";
import { MicLevelMeter } from "./MicLevelMeter";
import { TranscriptPreview } from "./TranscriptPreview";

export function CallPanel({ sessionId, transcript }: { sessionId: string; transcript: TranscriptItem[] }) {
  const mic = useMicrophone();
  const callClient = useMemo(() => createPlaceholderRealtimeCallClient(), []);
  const [callStatus, setCallStatus] = useState<CallConnectionStatus>(callClient.getStatus());

  useEffect(() => callClient.subscribe(setCallStatus), [callClient]);
  useEffect(
    () => () => {
      void callClient.disconnect();
    },
    [callClient],
  );

  async function connectVoice(): Promise<void> {
    if (mic.stream === null) {
      await mic.request();
    }
    await callClient.connect(sessionId, mic.stream ?? undefined);
  }

  return (
    <section className="card">
      <div className="card-body stack">
        <div className="panel-title">
          <h2>Call panel</h2>
          <Badge tone={callStatus === "connected" ? "success" : callStatus === "failed" ? "danger" : "warning"}>
            {callStatus}
          </Badge>
        </div>
        <div className="call-grid">
          <div className="stack">
            <div className="row">
              <Button type="button" onClick={() => void connectVoice()}>
                {mic.status === "idle" ? "Connect microphone" : "Connect voice"}
              </Button>
              <Button type="button" variant="secondary" onClick={mic.toggleMute} disabled={mic.stream === null}>
                {mic.muted ? "Unmute" : "Mute"}
              </Button>
            </div>
            <div aria-live="polite">
              <Badge tone={mic.status === "failed" ? "danger" : mic.status === "microphone_ready" ? "success" : "warning"}>
                Mic: {mic.status}
              </Badge>
            </div>
            {mic.error === null ? null : <ErrorBanner message={mic.error} />}
            <MicLevelMeter stream={mic.stream} />
          </div>
          <AgentAudioPanel status={callStatus} />
        </div>
        <TranscriptPreview items={transcript} />
      </div>
    </section>
  );
}
