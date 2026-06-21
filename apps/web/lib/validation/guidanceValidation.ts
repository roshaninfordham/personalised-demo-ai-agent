export type GuidanceValidationResult = {
  valid: boolean;
  error?: string;
  warning?: string;
};

const secretPattern = /(api_key|secret|token|password|private_key|client_secret|refresh_token|access_token)/i;

export function validateGuidance(value: string, maxBytes = 32 * 1024): GuidanceValidationResult {
  const bytes = new TextEncoder().encode(value).byteLength;
  if (bytes > maxBytes) return { valid: false, error: "Guidance is too large." };
  if (secretPattern.test(value)) {
    return {
      valid: false,
      error: "Guidance appears to contain a secret-like value. Remove credentials before continuing.",
    };
  }
  return { valid: true };
}
