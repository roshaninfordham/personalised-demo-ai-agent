"use client";

import { Input } from "../ui/Input";

export function UrlInput({
  value,
  onChange,
  error,
  warning,
}: {
  value: string;
  onChange: (value: string) => void;
  error: string | null;
  warning: string | null;
}) {
  const describedBy = [error === null ? null : "product-url-error", warning === null ? null : "product-url-warning"]
    .filter((item): item is string => item !== null)
    .join(" ");
  return (
    <div className="field">
      <label htmlFor="product-url">Product URL</label>
      <Input
        id="product-url"
        name="product_url"
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
        placeholder="https://example.com"
        aria-invalid={error !== null}
        aria-describedby={describedBy.length > 0 ? describedBy : undefined}
        autoComplete="url"
      />
      {error === null ? null : (
        <p id="product-url-error" className="field-error">
          {error}
        </p>
      )}
      {warning === null ? null : (
        <p id="product-url-warning" className="field-warning">
          {warning}
        </p>
      )}
    </div>
  );
}
