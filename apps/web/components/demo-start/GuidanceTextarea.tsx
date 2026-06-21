"use client";

import { Textarea } from "../ui/Textarea";

export function GuidanceTextarea({
  value,
  onChange,
  error,
}: {
  value: string;
  onChange: (value: string) => void;
  error: string | null;
}) {
  return (
    <div className="field">
      <label htmlFor="text-guidance">Text guidance</label>
      <Textarea
        id="text-guidance"
        name="text_guidance"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
        placeholder="Positioning notes, setup context, or restrictions. Do not paste secrets."
        aria-invalid={error !== null}
        aria-describedby={error === null ? undefined : "text-guidance-error"}
        rows={5}
      />
      {error === null ? null : (
        <p id="text-guidance-error" className="field-error">
          {error}
        </p>
      )}
    </div>
  );
}
