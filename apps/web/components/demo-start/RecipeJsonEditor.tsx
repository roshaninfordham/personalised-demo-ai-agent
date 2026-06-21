"use client";

import { Textarea } from "../ui/Textarea";
import { JsonValidationMessage } from "../ui/JsonValidationMessage";

export function RecipeJsonEditor({
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
      <label htmlFor="recipe-json">Recipe JSON</label>
      <Textarea
        id="recipe-json"
        name="recipe_json"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
        placeholder='{"recipe_name":"Founder Demo","demo_goal":"Show key dashboard value.","steps":[{"step_order":0,"step_key":"overview","goal":"Show overview"}]}'
        aria-invalid={error !== null}
        rows={8}
      />
      <JsonValidationMessage message={error} tone="error" />
    </div>
  );
}
