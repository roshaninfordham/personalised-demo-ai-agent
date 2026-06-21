"use client";

import { useEffect, useState, type CSSProperties } from "react";

import { createAudioLevelMeter } from "../../lib/media/audioLevelMeter";

export function MicLevelMeter({ stream }: { stream: MediaStream | null }) {
  const [level, setLevel] = useState(0);

  useEffect(() => {
    if (stream === null) {
      setLevel(0);
      return undefined;
    }
    const meter = createAudioLevelMeter(stream);
    meter.start(setLevel);
    return () => {
      meter.stop();
    };
  }, [stream]);

  return (
    <div className="field">
      <label>Microphone level</label>
      <div className="meter" aria-label={`Microphone level ${String(Math.round(level * 100))} percent`}>
        <span style={{ "--level": `${String(Math.round(level * 100))}%` } as CSSProperties} />
      </div>
    </div>
  );
}
