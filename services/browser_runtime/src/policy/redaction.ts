import { redactionRules } from "@live-demo-agent/policies";

export type RedactionResult = {
  redactedValue: unknown;
  applied: boolean;
  findings: { findingType: string; path?: string }[];
};

export function redactText(text: string): RedactionResult {
  let redacted = text;
  const findings: { findingType: string }[] = [];
  for (const pattern of redactionRules.patterns) {
    const regex = new RegExp(pattern.regex, "giu");
    const next = redacted.replace(regex, pattern.replacement);
    if (next !== redacted) findings.push({ findingType: pattern.finding_type });
    redacted = next;
  }
  redacted = redacted.replace(/\b(?:\d[ -]?){13,19}\b/gu, (value) => {
    if (!luhnValid(value)) return value;
    findings.push({ findingType: "credit_card" });
    return "[REDACTED_CREDIT_CARD]";
  });
  return { redactedValue: redacted, applied: findings.length > 0, findings };
}

export function redactJson(value: unknown): RedactionResult {
  const findings: { findingType: string; path?: string }[] = [];
  const sensitiveKeys = redactionRules.sensitive_keys as readonly string[];

  function visit(node: unknown, path: string, depth: number): unknown {
    if (depth > 10) {
      findings.push({ findingType: "redaction_input_too_deep", path });
      return "[REDACTED_TOO_DEEP]";
    }
    if (Array.isArray(node)) {
      return node.map((item, index) => visit(item, `${path}[${String(index)}]`, depth + 1));
    }
    if (typeof node === "object" && node !== null) {
      const output: Record<string, unknown> = {};
      for (const [key, child] of Object.entries(node)) {
        const normalizedKey = normalizeKey(key);
        const childPath = `${path}.${key}`;
        if (sensitiveKeys.some((sensitiveKey) => normalizedKey.includes(normalizeKey(sensitiveKey)))) {
          output[key] = "[REDACTED_SECRET]";
          findings.push({ findingType: "sensitive_key", path: childPath });
        } else {
          output[key] = visit(child, childPath, depth + 1);
        }
      }
      return output;
    }
    if (typeof node === "string") {
      const result = redactText(node);
      if (result.applied) {
        findings.push(...result.findings.map((finding) => ({ ...finding, path })));
      }
      return result.redactedValue;
    }
    return node;
  }

  const redactedValue = visit(value, "$", 0);
  return { redactedValue, applied: findings.length > 0, findings };
}

export function redactScreenshotMetadata(value: Record<string, unknown>): Record<string, unknown> {
  const redacted = redactJson(value);
  return {
    ...(redacted.redactedValue as Record<string, unknown>),
    contains_potential_sensitive_visual_data: redacted.applied,
    text_metadata_redacted: redacted.applied,
    visual_redaction_applied: false,
  };
}

function normalizeKey(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9]+/gu, "_");
}

function luhnValid(value: string): boolean {
  const digits = value.replace(/\D/gu, "");
  if (digits.length < 13 || digits.length > 19) return false;
  let sum = 0;
  let shouldDouble = false;
  for (let index = digits.length - 1; index >= 0; index -= 1) {
    let digit = Number(digits[index]);
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}
