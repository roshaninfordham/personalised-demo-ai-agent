"use client";

import { useState } from "react";

import { sendTextTurn, type TextTurnResponse } from "../../lib/api/demoSessionsApi";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

export function QuestionInput({
  sessionId,
  fallbackEventsEnabled = false,
  onFallbackTurn,
}: {
  sessionId: string;
  fallbackEventsEnabled?: boolean;
  onFallbackTurn?: (text: string, response: TextTurnResponse) => void;
}) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(): Promise<void> {
    const value = text.trim();
    if (value === "" || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await sendTextTurn(sessionId, value);
      if (fallbackEventsEnabled) onFallbackTurn?.(value, response);
      setText("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The agent could not answer that turn.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="stack">
      <div className="question-input">
        <Input
          value={text}
          onChange={(event) => {
            setText(event.target.value);
          }}
          placeholder="Ask the demo agent..."
          aria-label="Ask the demo agent"
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void submit();
            }
          }}
        />
        <Button
          type="button"
          onClick={() => {
            void submit();
          }}
          disabled={submitting || text.trim() === ""}
        >
          {submitting ? "Asking..." : "Ask"}
        </Button>
      </div>
      {error === null ? null : <div className="field-error">{error}</div>}
    </div>
  );
}
