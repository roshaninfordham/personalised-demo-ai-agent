"use client";

import { useEffect, useMemo, useState } from "react";

import { useMicrophone } from "../../hooks/useMicrophone";
import type { TextTurnResponse } from "../../lib/api/demoSessionsApi";
import type { EventConnectionStatus, TranscriptItem } from "../../lib/events/eventTypes";
import type { CallConnectionStatus } from "../../lib/media/mediaTypes";
import { createPlaceholderRealtimeCallClient } from "../../lib/media/webrtcClient";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { AgentAudioPanel } from "./AgentAudioPanel";
import { ErrorBanner } from "./ErrorBanner";
import { MicLevelMeter } from "./MicLevelMeter";
import { QuestionInput } from "./QuestionInput";
import { TranscriptPreview } from "./TranscriptPreview";

export function CallPanel({
  sessionId,
  transcript,
  eventStatus,
  onFallbackTextTurn,
}: {
  sessionId: string;
  transcript: TranscriptItem[];
  eventStatus: EventConnectionStatus;
  onFallbackTextTurn?: (text: string, response: TextTurnResponse) => void;
}) {
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
          <div>
            <h2>Assistant</h2>
            <span className="muted">Voice is optional locally. Text mode is always available.</span>
          </div>
          <Badge tone={callStatus === "connected" ? "success" : callStatus === "failed" ? "danger" : "warning"}>
            {callStatus === "connected" ? "voice connected" : "text mode active"}
          </Badge>
        </div>
        <QuestionInput
          sessionId={sessionId}
          fallbackEventsEnabled={eventStatus !== "connected"}
          {...(onFallbackTextTurn === undefined ? {} : { onFallbackTurn: onFallbackTextTurn })}
        />
        <details className="voice-details">
          <summary>Voice controls</summary>
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
        </details>
        <TranscriptPreview items={transcript} />
      </div>
    </section>
  );
}
