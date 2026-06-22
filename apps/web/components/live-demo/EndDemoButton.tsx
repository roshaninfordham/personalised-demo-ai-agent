"use client";

import { useState } from "react";

import { endDemoSession } from "../../lib/api/demoSessionsApi";
import { Button } from "../ui/Button";

export function EndDemoButton({ sessionId }: { sessionId: string }) {
  const [ending, setEnding] = useState(false);
  const [ended, setEnded] = useState(false);

  async function endDemo(): Promise<void> {
    if (ending || ended) return;
    setEnding(true);
    try {
      await endDemoSession(sessionId);
      setEnded(true);
    } finally {
      setEnding(false);
    }
  }

  return (
    <Button type="button" variant={ended ? "secondary" : "danger"} onClick={() => void endDemo()} disabled={ending || ended}>
      {ended ? "Demo ended" : ending ? "Ending..." : "End demo"}
    </Button>
  );
}
